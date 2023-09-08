class PDControlSystem:
    def __init__(self, kp, kd, threshold):
        self.kp = kp  # Proportional gain
        self.kd = kd  # Derivative gain
        self.threshold = threshold

    def calculate_error(self, setpoint, measured_value):
        error = setpoint - measured_value
        return error

    def calculate_error_derivative(self, prev_error, current_error, time_step):
        error_derivative = (current_error - prev_error) / time_step
        return error_derivative

    def run_control_system(self, setpoint, measured_value, prev_error, time_step):
        error = self.calculate_error(setpoint, measured_value)
        error_derivative = self.calculate_error_derivative(prev_error, error, time_step)

        control_output = self.kp * error + self.kd * error_derivative

        if control_output > self.threshold:
            return 3
        elif control_output < -self.threshold:
            return 1
        else:
            return 1 #safe 