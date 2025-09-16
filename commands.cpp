#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <arpa/inet.h>
#include <unistd.h>
#include <csignal>
#include <vector>
#include <poll.h>

#include <unitree/robot/go2/sport/sport_client.hpp>

bool stopped = false;
void sigint_handler(int sig) {
    if (sig == SIGINT) {
        std::cout << "\n🛑 SIGINT received, exiting..." << std::endl;
        stopped = true;
    }
}

// --- Command matching helper ---
bool match_command(const std::string &cmd, const std::vector<std::string> &keywords) {
    for (const auto &word : keywords) {
        if (cmd.find(word) != std::string::npos) return true;
    }
    return false;
}

// --- Helper: perform an action then rebalance ---
template<typename Func>
void do_action(Func action, unitree::robot::go2::SportClient &sport_client, int delay_ms = 1000) {
    action();
    std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
    sport_client.BalanceStand();
}

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " networkInterface" << std::endl;
        return -1;
    }

    signal(SIGINT, sigint_handler);

    // Initialize Unitree SDK
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(20.0f);
    sport_client.Init();

    std::cout << "🤖 Unitree Go2 SDK initialized." << std::endl;

    // Setup UDP socket
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Socket creation failed");
        return -1;
    }

    struct sockaddr_in servaddr {};
    socklen_t len = sizeof(servaddr);
    char buffer[1024];

    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(5005);

    if (bind(sockfd, (const struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("Bind failed");
        close(sockfd);
        return -1;
    }

    // Start in Pose mode
    std::cout << "Entering Pose mode..." << std::endl;
    sport_client.Pose(true);
    usleep(300000);

    std::cout << "🎧 Waiting for wake word..." << std::endl;

    bool active = false;
    auto lastWake = std::chrono::steady_clock::now();
    const int ACTIVE_WINDOW = 10; // seconds

    // ✅ Word lists
    std::vector<std::string> wake_words    = {"ego", "echo", "hey go", "hey ego", "wake", "he go", "ok go", "ok ego"};
    std::vector<std::string> stand_words   = {"stand up", "get up", "wake up", "rise", "on feet", "stand"};
    std::vector<std::string> sit_words     = {"sit", "sit down", "down", "rest", "take a seat"};
    std::vector<std::string> move_words    = {"move", "move forward", "walk", "march", "advance", "step"};
    std::vector<std::string> stop_words    = {"stop", "halt", "freeze", "pause", "stay"};
    std::vector<std::string> balance_words = {"balance", "steady", "stabilize", "hold"};
    std::vector<std::string> recover_words = {"recover", "get up again", "reset", "back up"};
    std::vector<std::string> shout_words   = {"shout", "thing", "yell", "loud", "scream"};

    // Poll setup for ESC key
    struct pollfd fds[1];
    fds[0].fd = STDIN_FILENO;
    fds[0].events = POLLIN;

    while (!stopped) {
        // ESC key handling
        if (poll(fds, 1, 10) > 0) {
            if (fds[0].revents & POLLIN) {
                char c;
                if (read(STDIN_FILENO, &c, 1) > 0 && c == 27) {
                    std::cout << "\n🚪 Escape pressed, exiting..." << std::endl;
                    break;
                }
            }
        }

        // UDP receive
        int n = recvfrom(sockfd, buffer, sizeof(buffer) - 1, MSG_DONTWAIT,
                         (struct sockaddr *)&servaddr, &len);
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
            perror("recvfrom failed");
            continue;
        }

        buffer[n] = '\0';
        std::string cmd(buffer);
        std::cout << "🗣️ Heard: " << cmd << std::endl;

        // ✅ Wake word detection
        if (match_command(cmd, wake_words)) {
            active = true;
            lastWake = std::chrono::steady_clock::now();
            std::cout << "🚀 Wake word detected! Performing wake-up wiggle..." << std::endl;
            continue;
        }

        if (!active) {
            std::cout << "💤 Ignored (waiting for wake word)." << std::endl;
            continue;
        }

        auto now = std::chrono::steady_clock::now();
        int elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - lastWake).count();
        if (elapsed > ACTIVE_WINDOW) {
            active = false;
            std::cout << "⏳ Listening window expired. Say wake word again." << std::endl;
            continue;
        }

        // --- Command mapping ---
        if (match_command(cmd, stand_words)) {
            std::cout << "🤖 Standing up..." << std::endl;
            do_action([&]{ sport_client.StandUp(); }, sport_client);
        }
        else if (match_command(cmd, sit_words)) {
            std::cout << "🤖 Sitting down..." << std::endl;
            do_action([&]{ sport_client.StandDown(); }, sport_client);
        }
        else if (match_command(cmd, move_words)) {
            std::cout << "🤖 Moving forward..." << std::endl;
            do_action([&]{ sport_client.Move(0.5, 0, 0); }, sport_client);
        }
        else if (match_command(cmd, stop_words)) {
            std::cout << "🛑 Stopping..." << std::endl;
            do_action([&]{ sport_client.StopMove(); }, sport_client);
        }
        else if (match_command(cmd, balance_words)) {
            std::cout << "⚖️ Balancing..." << std::endl;
            do_action([&]{ sport_client.BalanceStand(); }, sport_client);
        }
        else if (match_command(cmd, recover_words)) {
            std::cout << "🔄 Recovering..." << std::endl;
            do_action([&]{ sport_client.RecoveryStand(); }, sport_client);
        }
        else {
            std::cout << "❓ Unknown command: " << cmd << std::endl;
        }
    }

    close(sockfd);
    std::cout << "✅ Program exited cleanly." << std::endl;
    return 0;
}
