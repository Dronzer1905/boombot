import socket
import time
import pygame
import sys

ROBOT_IP = "192.168.137.60" 
PORT = 8080
DEADZONE = 0.2  

def get_proportional_value(axis_value):
    if abs(axis_value) < DEADZONE:
        return 0
    sign = 1 if axis_value > 0 else -1
    magnitude = (abs(axis_value) - DEADZONE) / (1.0 - DEADZONE)
    return int(sign * magnitude * 255)

def main():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("nO CONTROLLER FOND")
        sys.exit()
        
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Connected : {joystick.get_name()}")
    
    print(f"connect to robot at {ROBOT_IP}:{PORT}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0) 
        s.connect((ROBOT_IP, PORT))
        print("Connected successfully")
        
        last_command = ""
        
        while True:
            pygame.event.pump()
            
            raw_y = joystick.get_axis(1) #left Y
            raw_x = joystick.get_axis(0)  #left X
            raw_rot = joystick.get_axis(3) #right Y
            
            vx = get_proportional_value(-raw_y) 
            vy = get_proportional_value(raw_x)
            wz = get_proportional_value(raw_rot)
            command = f"{vx} {vy} {wz}\n"
            
            if command != last_command:
                s.sendall(command.encode('utf-8'))
                print(f"Sent Matrix Command: {command.strip()}")
                last_command = command               
            time.sleep(0.05) 
            
    except KeyboardInterrupt:
        print("\n manual exit")
    except Exception as e:
        print(f"\nconnection error: {e}")
        
    finally:
        try:
            s.sendall("0 0 0\n".encode('utf-8'))
            s.close()
        except:
            pass
        pygame.quit()

if __name__ == "__main__":
    main()