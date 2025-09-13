#include <iostream>
#include <unistd.h>
#include <signal.h>
#include <cmath>   // for sin() wave

#include <unitree/robot/go2/sport/sport_client.hpp>

bool stopped = false;

// Handle Ctrl+C
void sigint_handler(int sig)
{
    if (sig == SIGINT)
        stopped = true;
}

int main(int argc, char **argv)
{
    if (argc < 2)
    {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }

    // Initialize communication with Go2
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);

    // Sport client
    unitree::robot::go2::SportClient sport_client;
    sport_client.SetTimeout(10.0f);
    sport_client.Init();

    // Handle Ctrl+C
    signal(SIGINT, sigint_handler);

    std::cout << "Entering Pose mode..." << std::endl;
    sport_client.Pose(true);   // enter pose mode
    usleep(300000);            // 0.3s

    std::cout << "Preparing posture (front legs straightened a bit)..." << std::endl;

    std::cout << "Starting wiggle..." << std::endl;
    
    double pitch = -0.25;   // keep leaning back
    double roll  = 0.0;
    double yaw_amp = 0.05;  // wiggle amplitude (±0.25 rad ~ 14°)
    double freq = 3.0;      // wiggle frequency (Hz, ~3 wiggles/sec)

    for (int i = 0; i < 30 && !stopped; i++)  // about 10 sec
    {
        double t = i * 0.05;  // step time (50ms per loop)
        double yaw = yaw_amp * sin(2 * M_PI * freq * t);
        sport_client.Euler(roll, pitch, yaw);
        usleep(50000);  // 50 ms
    }

    std::cout << "Resetting Euler (back to neutral)..." << std::endl;
    sport_client.Euler(0.0, 0.0, 0.0);
    sleep(1);

    std::cout << "Exiting Pose mode..." << std::endl;
    sport_client.Pose(false);

    std::cout << "Done." << std::endl;
    return 0;
}
