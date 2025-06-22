std_msgs/Header header
builtin_interfaces/Time measuring_ts
builtin_interfaces/Time publish_ts
string frame_id
string child_frame_id
float32[] velocity
float32[] velocity_body
float32[] acceleration
float32[] ang_vel
bool is_slipping

geometry_msgs/Point position
geometry_msgs/Quaternion orientation_quat
geometry_msgs/Vector3 orientation_euler
float32[36] covariance
