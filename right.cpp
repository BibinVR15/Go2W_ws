#include <iostream>
#include <thread>
#include <chrono>
#include <csignal>
#include <unitree/robot/go2/sport/sport_client.hpp>

bool stopped = false;

void sigint_handler(int sig) {
    if (sig == SIGINT)
        stopped = true;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        return -1;
    }

    // Init SDK
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f);
    sport_client.Init();

    signal(SIGINT, sigint_handler);
    sport_client.BalanceStand();

    auto run_action = [&](auto action, const std::string &name) {
        if (stopped) return;
        std::cout << "▶️ Running action: " << name << std::endl;
        action();
        std::this_thread::sleep_for(std::chrono::seconds(1));

        // stop moving before balancing again
        sport_client.StopMove();
        std::this_thread::sleep_for(std::chrono::milliseconds(250));
        sport_client.BalanceStand();
        std::this_thread::sleep_for(std::chrono::milliseconds(250));
    };

    // Example: Move Right with slight rotation
    run_action([&](){ sport_client.Move(0.0, 0.0, -0.5); }, "Move Right");

    std::cout << "✅ Done. Robot is in Balance Stand mode." << std::endl;
    return 0;
}
