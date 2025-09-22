#include <iostream>
#include <filesystem>
#include <cstdlib>
#include <string>
#include <unistd.h>
#include <signal.h>
#include <cmath>
#include <vector>
#include <tuple>
#include <random>

#include <unitree/robot/go2/sport/sport_client.hpp>

namespace fs = std::filesystem;

bool stopped = false;

void sigint_handler(int sig) {
    if(sig == SIGINT)
        stopped = true;
}

// Play a specific audio file
void play_audio(const std::string &file_path) {
    std::string cmd = "aplay \"" + file_path + "\" &"; 
    (void)system(cmd.c_str());
}

// Helper: lean/sway motion for a given duration
void lean_motion(unitree::robot::go2::SportClient &client,
                 double pitch, double roll_amp, double yaw_amp, double duration_s) {
    const double dt = 0.05; // 50ms per step
    int steps = static_cast<int>(duration_s / dt);

    for(int i = 0; i < steps && !stopped; i++) {
        double t = i * dt;
        double roll = roll_amp * sin(2 * M_PI * 1.5 * t); 
        double yaw  = yaw_amp * sin(2 * M_PI * 1.5 * t);  
        client.Euler(roll, pitch, yaw);
        usleep(static_cast<useconds_t>(dt * 1e6));
    }
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

    // Enter Pose mode
    sport_client.Pose(true);
    usleep(500000);

    std::cout << "Playing audio..." << std::endl;
    play_audio("/home/verse/unitree_sdk2/example/go2w/minions/shout.wav");

    // --- Marching & lean sequence ---
    struct MotionStep { double pitch; double roll; double yaw; double duration; };
    std::vector<MotionStep> sequence = {
        {-0.25, 0.0, 0.0, 3.0},
        {0.15, 0.0, 0.0, 2.5},
        {-0.05, -0.2, 0.05, 3.0},
        {-0.05, 0.2, -0.05, 3.0},
        {-0.2, 0.0, 0.1, 2.5},
        {0.1, 0.0, -0.1, 2.5},
        {-0.15, -0.15, 0.0, 3.0},
        {-0.15, 0.15, 0.0, 3.0},
        {-0.1, 0.0, 0.0, 3.0},
        {-0.05, -0.2, 0.05, 3.0},
        {-0.05, 0.2, -0.05, 3.0},
        {-0.2, 0.0, 0.1, 2.5},
        {0.1, 0.0, -0.1, 2.5},
        {-0.15, -0.15, 0.0, 3.0},
        {-0.15, 0.15, 0.0, 3.0}
    };

    double elapsed = 0.0;
    for(auto &step : sequence) {
        if(stopped) break;
        lean_motion(sport_client, step.pitch, step.roll, step.yaw, step.duration);
        elapsed += step.duration;
        if(elapsed >= 39.0) break; // cap total routine to ~39s
    }

    // --- Falling steps: simulate a collapse ---
    std::cout << "Executing falling motion..." << std::endl;
    
    sport_client.Pose(false);
    sport_client.Move(0.0, 0.0, 0.0);

    std::cout << "Routine completed. Exiting program." << std::endl;

    return 0; // Exit cleanly
}
