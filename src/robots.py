import time,signal,os,sys
from sensor import Sensor

movement = True
battery_consumption = True

def battery_reset(signo,frame):
    global battery
    battery = 100
    global battery_consumption
    battery_consumption = True


def robot_info(signo,frame):
    print(" Identifier:",identifier," Position:",position," Battery:",battery)

def pause(signo,frame):
    global movement
    movement = False
    global battery_consumption
    battery_consumption = False
    print("Robot",identifier,"is stopped")

def resume(signo,frame):
    global movement
    movement = True
    global battery_consumption
    battery_consumption = True 
    signal.alarm(1)

def dec_bat(signo, frame):
    global battery
    if battery_consumption == True and battery > 0:
        battery -= 1
        signal.alarm(1)

def move_robot(direction):
    global battery
    if battery > 5:
        global position
        if direction == 'down':
            if position[0] == s._rows-1:
                print("Robot", identifier,"cannot move down.")
                print("KO")
            elif obstacle(position[0]+1,position[1]) == True:
                print("Robot",identifier,"cannot move down")
                print("KO")
            else:
                position = (position[0]+1 , position[1])
                print("OK")
                battery -=5

        elif direction == 'up':
            if position[0] == 0:
                print("Robot",identifier,"cannot move up.")
                print("KO")
            elif obstacle(position[0]-1,position[1]) == True:
                print("Robot",identifier,"cannot move up")
                print("KO")
            else:
                position = (position[0]-1 , position[1])
                print("OK")
                battery -=5

        elif direction == 'left':
            if position[1] == 0:
                print("Robot",identifier,"cannot move left.")
                print("KO")
            elif obstacle(position[0],position[1]-1) == True:
                print("Robot",identifier,"cannot move left")
                print("KO")
            else:
                position = (position[0] , position[1]-1)
                print("OK")
                battery -=5

        elif direction == 'right':
            if position[1] == s._columns-1:
                print("Robot",identifier,"cannot move right.")
                print("KO")
            elif obstacle(position[0],position[1]+1) == True:
                print("Robot",identifier,"cannot move right")
                print("KO")
            else:
                position = (position[0] , position[1]+1)
                print("OK")
                battery -=5
        else:
            print("Invalid Direction")
    else:
        print(f"Robot {identifier} cannot move {direction} due to battery\nKO")

def treasure():
    if (s.with_treasure(position[0],position[1])):
        print("Treasure.")
    else:
        print("Water.")

def obstacle(pos1,pos2):
    if (s.with_obstacle(pos1,pos2)):
        return True
    else:
        return False



def main():
    global position
    position = (0,0) 
    global battery
    battery = 100
    FBool = False
    IBool = False
    while len(sys.argv)>=2:
        if sys.argv[1] == '1' or sys.argv[1] == '2' or sys.argv[1] == '3' or sys.argv[1] == '4' or sys.argv[1] == '5' or sys.argv[1] == '6' or sys.argv[1] == '7' or sys.argv[1] == '8' or sys.argv[1] == '9' or sys.argv[1] == '10':
            global identifier
            identifier = int(sys.argv[1])
            sys.argv.pop(1)
            IBool = True
        elif sys.argv[1] == "-b":
            battery = int(sys.argv[2])
            sys.argv.pop(1)
            sys.argv.pop(1)
        elif sys.argv[1] == "-f":
            global filename
            filename = sys.argv[2]
            global s
            s = Sensor(filename)
            sys.argv.pop(1)
            sys.argv.pop(1)
            FBool = True
        elif sys.argv[1] == "-pos":
            if len(sys.argv[1:])<3:
                print("Enter a valid position")
                sys.exit(1)

            elif len(sys.argv[1:])>3:
                if identifier != None and sys.argv[4] == ('1' or '2' or '3' or '4' or '5' or '6' or '7' or '8' or '9' or '10'):
                    print("Please dont enter more than 2 coordinates for the position")
                    print("Example: -pos 1 2")
                    sys.exit(1)

            elif sys.argv[2] == '0' and sys.argv[3] == '0':
                print("Invalid initial position")
                sys.exit(1)

            position = (int(sys.argv[2]),int(sys.argv[3])) 
            sys.argv.pop(1)
            sys.argv.pop(1)
            sys.argv.pop(1)
        else:
            print("Invalid input:",sys.argv[1])
            sys.exit(1)

    if IBool == False:
       if FBool == False:
           print("Please enter an identifier and a file for the room")
       else:
           print("Please enter an identifier")
       sys.exit(1)
            
    if FBool == False:
        print("Enter a file for the room") 
        sys.exit(1)
    
    if position[0]< 0 or position[0]> s.dimensions()[0]-1 or position[1]< 0 or position[1] > s.dimensions()[1]-1:
        print("Enter a position in the range of the dimensions of the room.")    
        sys.exit(1)
    elif obstacle(position[0],position[1]) == True:
        print("Enter a position where there is not an obstacle.")
        sys.exit(1)

    signal.signal(signal.SIGUSR1,battery_reset)
    signal.signal(signal.SIGINT, pause)
    signal.signal(signal.SIGQUIT, resume)  
    signal.signal(signal.SIGTSTP, robot_info) 
    signal.signal(signal.SIGALRM, dec_bat)
    signal.alarm(1)
    
    print("PID: %i" % os.getpid())
    EBool = False
    while EBool == False:
        command = input()
        if len(command.split()) == 1:
            if command == 'bat' or command == 'Bat':
                print('Battery: ', battery)
            
            elif command == 'pos' or command == 'Pos':
                print('Position: ', position)
            
            elif command == 'tr' or command == 'Tr':
                treasure()

            elif command == 'exit':
                print('Battery:',battery,'and Position:',position)
                sys.exit(1) 
            else:
                print("Invalid Input")
            
        elif len(command.split()) == 2:
            if command.split()[0] == 'mv':
                move = command.split()[1]
                move_robot(move)
            else:
                print("Invalid Input")

        else:
            print("Invalid Input")
        
if __name__ == '__main__':
    main()        

