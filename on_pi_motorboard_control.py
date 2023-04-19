# import ev3dev.ev3 as ev3
from time import sleep
import os
import csv
from raspberryPiExample.motors import Motors
import raspberryPiExample.test as motorlib


class PiMotorController():
    # expected input: might be come 7x7 (7+1 = 2x4)
    '''
    [['0', '0', '0', '0', '0'],
    ['1', '0', '1', '1', '1'],
    ['1', '0', '1', '0', '1'],
    ['1', '1', '1', '0', '1'],
    ['0', '0', '0', '0', '0'],
    ['0', '0', '0', '0', '0'],
    ['1', '1', '1', '1', '1'],
    ['1', '0', '0', '0', '1'],
    ['0', '1', '1', '1', '0'],
    ['0', '0', '0', '0', '0'],
    ['0', '0', '0', '0', '0'],
    ['1', '1', '1', '1', '1'],
    ['0', '0', '1', '0', '1'],
    ['0', '0', '1', '1', '1'],
    ['0', '0', '0', '0', '0']]
    '''
    # need parser to convert '10101' to: lists of (slide index, color code) pairs
    '''
    [
        [(0, 1), (1, 0), (2, 1), (3, 0), (4, 1)], ...
    ]
    '''
    # from slide index and color code, determine: motor direction
    # 'push all, sleep (wait for motors), pull back all, sleep (wait for motors)'
    # that is for each step / row of dominos to be placed
    def __init__(self, brick_index: int, motor_speed=30, motor_runtime=1000) -> None:
        self.brick_index = brick_index
        self.motor_speed = motor_speed
        self.motor_runtime = motor_runtime
        # self.motor_complete = False
        self.slide_motors = Motors()
        self.plan = []
    
    def spin(self, motor, forward: bool):
        speed = self.motor_speed
        if not forward:
            speed = -speed
        if not self.motor_complete:
            if not motor.connected:
                return
        # motor.run_timed(speed_sp=speed, time_sp=self.motor_runtime, stop_action='brake')
        motorlib.spin(motor, speed, self.motor_runtime)
    
    def action_decider(self, slide_index: int, color_code: int) -> tuple:
        '''
        Target Input: (0, 1) or (4, 0)
        Target Output: (1, False) or (5, True)

        Since: motor port 0 is reserved for backplate movements motor
        '''
        return (slide_index + 1, color_code == 0)

    def decompose_plan(self, row: list) -> list:
        '''
        Target Input: ['0', '1', '0', '0', '1']
        Target Output: [(0, 0), (1, 1), (2, 0), (3, 0), (4, 1)]
        '''
        pairs = []
        for i in range(len(row)):
            pairs.append(
                (i, int(row[i]))
            )
        return pairs
    
    def spin_all_motors(self, motors: list, forward: bool):
        for motor in motors:
            self.spin(motor, forward)
    
    def step(self, row: list):
        slide_color_pairs = self.decompose_plan(row)
        forward_motors = []
        backward_motors = []
        for pair in slide_color_pairs:
            (motor, forward) = self.action_decider(pair[0], pair[1])
            if forward:
                forward_motors.append(motor)
            else:
                backward_motors.append(motor)
        self.spin_all_motors(forward_motors, True)
        self.spin_all_motors(backward_motors, False)
        sleep(1)
        self.spin_all_motors(forward_motors, False)
        self.spin_all_motors(backward_motors, True)
        sleep(1)
    
    def execute_plan(self, input: list=None):
        plan = None
        if input is None:
            plan = self.plan
        else:
            plan = input
        for row in plan:
            self.step(row)

    def load_plan(self, path: str) -> list:
        plan = list(csv.reader(
            open(path)
        ))
        self.plan = plan
        return plan

# TODO: replace forward: bool with direction enum/str flags for better modularity? 


if __name__ == '__main__':
    brick = PiMotorController(0)
    # TODO: add flags to make it read a plan loaded / ssh'd into its directory
    plan_path = os.path.join("sdp6plan", "testplan1.csv")
    brick.load_plan(plan_path)
    brick.execute_plan()


