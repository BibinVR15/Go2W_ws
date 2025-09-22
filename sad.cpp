#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <string>
#include <unistd.h>
#include <signal.h>
#include <cmath>
#include <random>
#include <sys/wait.h>

#include <unitree/robot/go2/sport/sport_client.hpp>

namespace fs = std::filesystem;

bool stopped = false;
pid_t audio_pid = -1;

void sigint_handler(int sig) {
    if(sig == SIGINT) {
        stopped = true;
        if(audio_pid > 0) kill(audio_pid, SIGTERM);
    }
}

// Pick a random audio file from folder
std::string pick_random_audio(const std::string &folder_path) {
    std::vector<std::string> files;
    for(const auto &entry : fs::directory_iterator(folder_path)) {
        if(entry.is_regular_file()) {
            auto ext = entry.path().extension().string();
            if(ext == ".wav" || ext == ".mp3") {
                files.push_back(entry.path().string());
            }
        }
    }
    if(files.empty()) {
        std::cerr << "⚠️ No audio files in " << folder_path << std::endl;
        return "";
    }
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, files.size()-1);
    return files[dist(gen)];
}

// Play audio (foreground process we can wait on)
pid_t play_audio(const std::string &file_path) {
    pid_t pid = fork();
    if(pid == 0) {
        execlp("aplay", "aplay", file_path.c_str(), (char*)NULL);
        _exit(1);
    }
    return pid;
}

int main(int argc, char **argv) {
    if(argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        return -1;
    }

    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f);
    sport_client.Init();

    signal(SIGINT, sigint_handler);

    std::cout << "Entering Pose mode..." << std::endl;
    sport_client.Pose(true);
    usleep(300000);

    // 🎵 Pick random audio
    std::string chosen = pick_random_audio("/home/verse/unitree_sdk2/example/go2w/zhazha/sad");
    if(chosen.empty()) return -1;

    std::cout << "🔊 Playing: " << chosen << std::endl;

    // Start audio
    audio_pid = play_audio(chosen);

    // Wiggle loop while audio plays
    double pitch = 0.35;
    double yaw_amp = 0.04;
    double freq = 1.5;

    // Random roll generator
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<double> roll_dist(-0.3, 0.3); // small tilt range
    double roll = 0.0;
    int roll_update_interval = 15; // update roll every 15 cycles

    int i = 0;
    while(!stopped) {
        int status;
        pid_t result = waitpid(audio_pid, &status, WNOHANG);
        if(result == audio_pid) break; // audio finished

        double t = i * 0.05;
        double yaw = yaw_amp * sin(2 * M_PI * freq * t);

        // Occasionally refresh roll with a new random value
        if(i % roll_update_interval == 0) {
            roll = roll_dist(gen);
        }

        sport_client.Euler(roll, pitch, yaw);
        usleep(50000);
        i++;
    }

    // Final look-up pose
    sport_client.Euler(0.0, 0.0, 0.0);
    std::cout << "✅ Audio finished. Robot stays looking up." << std::endl;

    return 0;
}
