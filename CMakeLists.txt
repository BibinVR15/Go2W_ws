add_executable(go2w_sport_client go2w_sport_client.cpp)
target_link_libraries(go2w_sport_client unitree_sdk2)

add_executable(go2w_stand_example go2w_stand_example.cpp)
target_link_libraries(go2w_stand_example unitree_sdk2)

add_executable(pose pose.cpp)
target_link_libraries(pose unitree_sdk2)

add_executable(sing sing.cpp)
target_link_libraries(sing unitree_sdk2)

add_executable(commands commands.cpp)
target_link_libraries(commands unitree_sdk2)

add_executable(move move.cpp)
target_link_libraries(move unitree_sdk2)

add_executable(right right.cpp)
target_link_libraries(right unitree_sdk2)

add_executable(left left.cpp)
target_link_libraries(left unitree_sdk2)

add_executable(back back.cpp)
target_link_libraries(back unitree_sdk2)

add_executable(talk talk.cpp)
target_link_libraries(talk unitree_sdk2)

add_executable(answer answer.cpp)
target_link_libraries(answer unitree_sdk2)

add_executable(sad sad.cpp)
target_link_libraries(sad unitree_sdk2)

add_executable(my_name myname.cpp)
target_link_libraries(my_name unitree_sdk2)
