# The state of each joint (revolute or prismatic) is defined by:
#  * the control mode (csp 0, cst 1)
#  * the position of the joint (rad or m),
#  * the velocity of the joint (rad/s or m/s),
#  * the effort that is applied in the joint (Nm or N),
#  * the position of the motor (rad or m),
#  * the velocity of the motor (rad/s or m/s),
#  * the current of the motor (A),
#  * the error_code of the joint.      
#
# TODO: Error code description or joint error code page

std_msgs/Header header

string[] name
uint32[] mode
float64[] position
float64[] velocity
float64[] effort
float64[] motor_position
float64[] motor_velocity
float64[] motor_current
uint32[] error_code

