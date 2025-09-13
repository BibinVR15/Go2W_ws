#include <iostream>
#include <unistd.h>
#include <signal.h>
#include <cmath>
#include <thread>   // for std::thread
#include <cstdlib>  // for system()

#include <unitree/robot/go2/sport/sport_client.hpp>

bool stopped = false;

void sigint_handler(int sig)
{
    if (sig == SIGINT)
        stopped = true;
}

// Async TTS function
void speak_text(const std::string &text)
{
    std::string cmd = "espeak -s 200 -p 80 \"" + text + "\" &"; 
    system(cmd.c_str());
}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }

    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);

    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f);
    sport_client.Init();

    signal(SIGINT, sigint_handler);

    std::cout << "Entering Pose mode..." << std::endl;
    sport_client.Pose(true);
    // Start "ZHA ZHA!" asynchronously
    std::thread audio_thread(speak_text, "ZHA ZHA!");
    usleep(300000);

    std::cout << "Starting wiggle with audio..." << std::endl;

    

    double pitch = -0.25;
    double roll  = 0.0;
    double yaw_amp = 0.05;
    double freq = 3.0;

    for (int i = 0; i < 30 && !stopped; i++)
    {
        double t = i * 0.05;
        double yaw = yaw_amp * sin(2 * M_PI * freq * t);
        sport_client.Euler(roll, pitch, yaw);
        usleep(50000);
    }

    if (audio_thread.joinable())
        audio_thread.join();

    std::cout << "Resetting Euler..." << std::endl;
    sport_client.Euler(0.0, 0.0, 0.0);
    sleep(1);

    std::cout << "Exiting Pose mode..." << std::endl;
    sport_client.Pose(false);

    std::cout << "Done." << std::endl;
    return 0;
}
