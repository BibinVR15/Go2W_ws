#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <string>
#include <unistd.h>
#include <signal.h>
#include <cmath>

#include <unitree/robot/go2/sport/sport_client.hpp>

namespace fs = std::filesystem;

bool stopped = false;

void sigint_handler(int sig) {
    if(sig == SIGINT)
        stopped = true;
}

// Play a specific audio file
void play_audio(const std::string &file_path) {
    std::string cmd = "aplay \"" + file_path + "\" &"; // run in background
    (void)system(cmd.c_str());
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

    std::cout << "Starting wiggle and playing specific audio..." << std::endl;

    double pitch = -0.25;
    double roll  = 0.0;
    double yaw_amp = 0.05;
    double freq = 3.0;

    // Play the specific audio file
    play_audio("/home/verse/unitree_sdk2/example/go2w/zhazha/happy/h2.wav");

    for(int i = 0; i < 30 && !stopped; i++) {
        double t = i * 0.05;
        double yaw = yaw_amp * sin(2 * M_PI * freq * t);
        sport_client.Euler(roll, pitch, yaw);
        usleep(50000);
    }

    sport_client.Euler(0.0, -0.25, 0.0);
    return 0;
}
