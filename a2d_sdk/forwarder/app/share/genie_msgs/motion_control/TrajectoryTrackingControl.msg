std_msgs/Header header # frame id unused, timestamp sending time

# Control group information: std::vector<std::vector<RetargetInfo>> [time][group]
# Requirements for trajectory RetargetInfo:
# group_id, frame_id, control_mode, control_type cannot change within a trajectory, only read first frame
# group_id must be unique across different groups

RetargetInfoArray[] retarget_groups_trajectory
float64 trajectory_reference_time

string[] joint_names
float64[] joint_states