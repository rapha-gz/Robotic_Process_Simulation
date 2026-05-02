import time,signal,os,sys
from sensor import Sensor

class rob:
    def __init__(self):
        self.id = 0
        self.pid = 0
        self.pos = ()
        self.last_pos = ()
        self.obstacle = ()
        self.last_treasure = False
        self.readpipe = 0
        self.writepipe = 0

def battery_replenish(signo,frame):
    print("")
    print("Repleneshing batteries...")
    for i in range(len(factory)):
        os.kill(factory[i].pid,signal.SIGUSR1)
    print("Command:")

def robots_info(signo,frame):
    print("")
    for i in range(len(factory)):
        batt = "\n"
        os.write(parentw_pipes[i], batt.encode())
        reaction = os.read(parentr_pipes[i],1024).decode()
        print(reaction.strip().replace("\nInvalid Input",""))
    print("Command:")

def exit_program(signo,frame):
    print("\nBefore exiting...")
    for i in range(len(factory)):
        ext = "exit\n"
        os.write(parentw_pipes[i],ext.encode())
        pid_fin, status = os.wait()
        if os.WIFEXITED(status):
            exreaction = os.read(parentr_pipes[i],1024).decode()   
            code = os.WEXITSTATUS(status)
            new = exreaction.strip().replace(f"Robot {i+1} is stopped\n","")
            print(f"Robot {i+1} with PID:{pid_fin} exits with code: {os.WEXITSTATUS(status)}, {new}.")   
    sys.exit(1)

def print_room(room):
    print("Our information so far:")
    for row in room:
        for cell in row:
            print(cell, end=' ')
        print()

def update_map(robot,treasure, obstacle, room, s):
    if robot.last_pos != robot.pos and len(robot.last_pos)>0:
        last_x = int(robot.last_pos[0])
        last_y = int(robot.last_pos[1])
        
        if robot.last_treasure == True:
            room[last_x][last_y] = "T"
        else:
            room[last_x][last_y] = "-"
    if robot.last_pos == robot.pos and treasure == False:
        room[robot.pos[0]][robot.pos[1]] 
        
    if obstacle == True:
            room[robot.obstacle[0]][robot.obstacle[1]] = "X"

    if treasure == True or robot.pos in treasure_positions_list:
        x = int(robot.pos[0])
        y = int(robot.pos[1])
        room[x][y] = "RT"
        robot.last_treasure = True   

   
    else:
        x = int(robot.pos[0])
        y = int(robot.pos[1])
        room[x][y] = "R"
        robot.last_treasure = False  


def main():
    while len(sys.argv)>=2:
        match sys.argv[1]:
            case '-room':
                global rm_file
                rm_file = sys.argv[2]
                global s
                s = Sensor(rm_file)
                n_treasures = s._num_treasures
                n_treasures_found = 0
                sys.argv.pop(1)
                sys.argv.pop(1)

            case "-robots":
                with open(sys.argv[2], 'r') as file:
                    lines = file.readlines()
                    global factory
                    factory = [] 
                    for i in range(len(lines)):
                        r = rob()
                        r.bat = 100
                        r.id = i+1
                        rdimensions = lines[i].replace('(', '').replace(')', '').replace('\n','').split(',')
                        r.pos =(int(rdimensions[0]),int(rdimensions[1]))  
                        factory.append(r)
                sys.argv.pop(1)
                sys.argv.pop(1)
            case _:
                print("Invalid input:",sys.argv[1])
                sys.exit(1)

    room = []  
    for i in range(s._rows):
        room.append([])
        for j in range(s._columns):
            room[i].append('?')

    for i in range(len(factory)):
        x = int(factory[i].pos[0])
        y = int(factory[i].pos[1])
        room[x][y] = "R"
    print_room(room)

    for l in range(len(factory)):
        if int(factory[l].pos[0]) < 0 or int(factory[l].pos[0]) >= s.dimensions()[0] or int(factory[l].pos[1]) < 0 or int(factory[l].pos[1]) >= s.dimensions()[1]:
            print("Position of the robot "+str(factory[l].id)+" out of room")
            sys.exit(1)

    for j in range(len(factory)):
        for k in range(len(factory)-1-j):
            if factory[j].pos == factory[k+1+j].pos:
                print("Invalid position of robot "+ str(factory[j].id)+" and robot "+str(factory[k+1+j].id)) 
                sys.exit(1)
            k=0

    global parentr_pipes
    global parentw_pipes
    global childrenr_pipes
    global childrenw_pipes
    global treasure_positions_list
    parentr_pipes = []
    parentw_pipes = []  
    childrenr_pipes = []
    childrenw_pipes = []    
    treasure_positions_list = []  
    for m in range(len(factory)):
        rc_pipe,wp_pipe = os.pipe()
        rp_pipe,wc_pipe = os.pipe()
        factory[m].readpipe = rc_pipe
        factory[m].writepipe = wc_pipe  
        parentr_pipes.append(rp_pipe)
        parentw_pipes.append(wp_pipe)
        pid = os.fork()
        if pid == 0:
            os.close(rp_pipe)
            os.close(wp_pipe)
            os.dup2(factory[m].readpipe, sys.stdin.fileno())
            os.dup2(factory[m].writepipe, sys.stdout.fileno())
            try:
                python_interpreter = "/usr/bin/python3"
                script_path = os.path.join(os.getcwd(), "robots.py")
                arguments = [python_interpreter,script_path,str(factory[m].id),'-f',rm_file,"-pos",str(factory[m].pos[0]),str(factory[m].pos[1])]
                os.execv(python_interpreter,arguments)  
                
            except OSError as e:
                print(e)
                print("Error with execl:{e}")
                sys.exit(1)
        else:
            os.close(factory[m].readpipe)  
            os.close(factory[m].writepipe)
            factory[m].pid = pid


    signal.signal(signal.SIGTSTP, robots_info)
    signal.signal(signal.SIGINT, exit_program)
    signal.signal(signal.SIGQUIT, battery_replenish)   

    exit_ = False
    print("Parent PID:",os.getpid())
    for i in range(len(factory)):
        pids = os.read(parentr_pipes[i], 1024).decode()
        print(f"Robot {i+1} {pids.strip()} Position: {factory[i].pos}")

    for i in range(len(factory)):
        ObBool = False
        treasure = "tr\n"
        os.write(parentw_pipes[i], treasure.encode())
        treaction = os.read(parentr_pipes[i],1024).decode()
        if treaction.strip() == 'Treasure.':
            print("Robot ", j+1 ," found a treasure in its initial position!")
            n_treasures_found +=1
            TrBool = True
            treasure_positions_list.append(factory[i].pos)
            update_map(factory[i],TrBool, ObBool, room, s)
        else:
            TrBool = False
            update_map(factory[i],TrBool,ObBool,room,s)
    print_room(room)


    while exit_ == False:
        command = input("Command: ")
       #if command == 'print' and len(command.split()) == 1:
        if command == "":
            pass
        elif command == 'exit' and len(command.split()) == 1:
            exit_ = True
            print("Before exiting...")
            for i in range(len(factory)):
                ext = "exit\n "
                os.write(parentw_pipes[i],ext.encode())
                pid_fin, status = os.wait()
                if os.WIFEXITED(status):
                    code = os.WEXITSTATUS(status)
                    print(f"Child {pid_fin} exit code: {os.WEXITSTATUS(status)}") 
            sys.exit(1)
        
        elif command.split()[0] == 'bat' and len(command.split()) == 2:
            if command.split()[1] == 'all': #bat all
                for i in range(len(factory)):
                    batt = "bat\n"
                    os.write(parentw_pipes[i], batt.encode())
                    reaction = os.read(parentr_pipes[i],1024).decode()
                    print("Robot ", i+1,"PID:",factory[i].pid,"status:", reaction.strip())

            elif command.split()[1].isdigit() == True and int(command.split()[1]) in range(1,len(factory)+1):
                batt = "bat\n"
                os.write(parentw_pipes[int(command.split()[1])-1], batt.encode())
                reaction = os.read(parentr_pipes[int(command.split()[1])-1],1024).decode()
                print("Robot", command.split()[1],"status:", reaction.strip())
            else:
                print("Invalid Input:",command.split()[1])      

        elif command.split()[0] == 'pos' and len(command.split()) == 2:  
            if command.split()[1] == 'all':
                for i in range(len(factory)):
                    print("Robot ", i+1,"PID:",factory[i].pid,"status:",factory[i].pos)  

            elif command.split()[1].isdigit() == True and int(command.split()[1]) in range(1,len(factory)+1):
                print("Position of Robot", command.split()[1], ":", factory[int(command.split()[1])-1].pos)
            
            else:
                print("Invalid Input")    

        elif command.split()[0] == 'suspend' and len(command.split()) == 2:  
            if command.split()[1] == 'all':
                for i in range(len(factory)):
                    os.kill(factory[i].pid, signal.SIGINT)
                    esp="\n"
                    os.write(parentw_pipes[i],esp.encode())
                    stopreaction = os.read(parentr_pipes[i],1024).decode()
                    print(stopreaction.strip().replace("\nInvalid Input",""))

            elif command.split()[1].isdigit() == True and int(command.split()[1]) in range(1,len(factory)+1):
                os.kill(factory[int(command.split()[1])-1].pid, signal.SIGINT)
                esp="\n"
                os.write(parentw_pipes[int(command.split()[1])-1],esp.encode())
                stopreaction = os.read(parentr_pipes[int(command.split()[1])-1],1024).decode()
                print(stopreaction.strip().replace("\nInvalid Input",""))
                
            else:
                print("Invalid Input")    

        elif command.split()[0] == 'resume' and len(command.split()) == 2:  
            if command.split()[1] == 'all':
                for i in range(len(factory)):
                    os.kill(factory[i].pid, signal.SIGQUIT)
            elif command.split()[1].isdigit() == True and int(command.split()[1]) in range(1,len(factory)+1):
                os.kill(factory[int(command.split()[1])].pid,signal.SIGQUIT) 

            else:
                print("Invalid Input")   

        elif command.split()[0] == 'mv' and len(command.split()) == 3:
            if command.split()[1] == 'all': 
                for j in range(len(factory)):
                    ObBool = False
                    TrBool = False
                    Collision_Bool = False
                    for i in range(len(factory)):
                        if command.split()[2] == "up":
                            factory[j].obstacle = (factory[j].pos[0]-1,factory[j].pos[1]) 
                            if j+1 == factory[i].id:
                                pass
                            elif int(factory[j].pos[0])-1 == int(factory[i].pos[0]) and factory[j].pos[1] == factory[i].pos[1]:
                                print("If this movement is done robot ",j+1," and robot ",i+1 ," would collide")  
                                Collision_Bool = True
                                factory[j].last_pos = factory[j].pos  

                        elif command.split()[2] == "down":
                            factory[j].obstacle = (factory[j].pos[0]+1,factory[j].pos[1]) 
                            if j+1 == factory[i].id:
                                pass
                            elif int(factory[j].pos[0])+1 == int(factory[i].pos[0]) and factory[j].pos[1] == factory[i].pos[1]:
                                print("If this movement is done robot ",j+1," and robot ",i+1 ," would collide")  
                                Collision_Bool = True
                                factory[j].last_pos = factory[j].pos  

                        elif command.split()[2] == "left":
                            factory[j].obstacle = (factory[j].pos[0],factory[j].pos[1]-1) 
                            if command.split()[1] == factory[i].id:
                                pass
                            elif int(factory[j].pos[1])-1 == int(factory[i].pos[1]) and factory[j].pos[0] == factory[i].pos[0]:
                                print("If this movement is done robot ",j+1," and robot ",i+1 ," would collide")  
                                Collision_Bool = True
                                factory[j].last_pos = factory[j].pos  

                        elif command.split()[2] == "right":
                            factory[j].obstacle = (factory[j].pos[0],factory[j].pos[1]+1) 
                            if command.split()[1] == factory[i].id:
                                pass
                            elif int(factory[j].pos[1])+1 == int(factory[i].pos[1]) and factory[j].pos[0] == factory[i].pos[0]:
                                print("If this movement is done robot ",j+1," and robot ",i+1 ," would collide")  
                                Collision_Bool = True
                                factory[j].last_pos = factory[j].pos  

                        else:
                            print("Invalid direction")
                            Collision_Bool = True
                            
                    if Collision_Bool == False:
                        factory[j].last_pos = factory[j].pos  
                        movement = f"mv {command.split()[2]}\n"
                        os.write(parentw_pipes[j], movement.encode())
                        reaction = os.read(parentr_pipes[j],1024).decode()
                        if reaction.strip() == 'OK':
                            posi = "pos\n"
                            os.write(parentw_pipes[j], posi.encode())
                            rposi = os.read(parentr_pipes[j],1024).decode()
                            factory[j].pos = (int(rposi.strip().replace("Position:  (","").split(",")[0]),int(rposi.strip().replace(" ","").split(",")[1].replace(")","")))
                            treasure = "tr\n"
                            os.write(parentw_pipes[j], treasure.encode())
                            treaction = os.read(parentr_pipes[j],1024).decode()
                            if treaction.strip() == 'Treasure.':
                                if factory[j].pos not in treasure_positions_list:
                                    print("Robot ", j+1 ," found a treasure!")
                                    print("Robot ",j+1," status: ",reaction.strip())
                                    treasure_positions_list.append(factory[j].pos)
                                    n_treasures_found +=1
                                    TrBool = True 
                                    factory[j].last_treasure = False
                                    update_map(factory[j],TrBool,ObBool,room,s)
                                    if n_treasures == n_treasures_found:
                                        print("All treasures found!")
                                        print("Before exiting...")
                                        for i in range(len(factory)):
                                            ext = "exit\n"
                                            os.write(parentw_pipes[i],ext.encode())
                                            pid_fin, status = os.wait()
                                            if os.WIFEXITED(status):
                                                exreaction = os.read(parentr_pipes[i],1024).decode()   
                                                code = os.WEXITSTATUS(status)
                                                new = exreaction.strip().replace(f"Robot {i+1} is stopped\n","")
                                                print(f"Robot {i+1} with PID:{pid_fin} exits with code: {os.WEXITSTATUS(status)}, {new}.")   
                                                
                                        print_room(room)
                                        sys.exit(1)
                                else:
                                    TrBool = True
                            else:
                                print("Robot ",j+1," status: ",reaction.strip())

                        elif reaction.strip() == f"Robot {str(j+1)} cannot move {command.split()[2]}\nKO" :
                            print("Robot "+ str(j+1) + " cannot move " + command.split()[2],"due to obstacle.")
                            ObBool = True

                        elif reaction.strip() == f"Robot {str(j+1)} cannot move {command.split()[2]}.\nKO":
                            print("Robot "+ str(j+1) + " cannot move " + command.split()[2],"due to wall.")

                        elif reaction.strip() == f"Robot {str(j+1)} cannot move {command.split()[2]} due to battery\nKO" :
                            print("Robot "+ str(j+1) + " cannot move" + command.split()[2],"due to battery.")

                    update_map(factory[j],TrBool, ObBool, room, s)
                print_room(room)  

            elif command.split()[1].isdigit() == True and int(command.split()[1]) in range(1,len(factory)+1):
                Collision_Bool = False
                TrBool = False
                ObBool = False
                for i in range(len(factory)):
                    if command.split()[2] == "up":
                        factory[int(command.split()[1])-1].obstacle = (factory[int(command.split()[1])-1].pos[0]-1,factory[int(command.split()[1])-1].pos[1]) 
                        if command.split()[1] == factory[i].id:
                                pass
                        elif factory[int(command.split()[1])-1].pos[0]-1 == factory[i].pos[0] and factory[int(command.split()[1])-1].pos[1] == factory[i].pos[1]:
                            print("If this movement is done robot ",command.split()[1]," and robot ",i+1 ," would collide")  
                            Collision_Bool = True
                            factory[int(command.split()[1])-1].last_pos = factory[int(command.split()[1])-1].pos  

                    elif command.split()[2] == "down":
                        factory[int(command.split()[1])-1].obstacle = (factory[int(command.split()[1])-1].pos[0]+1,factory[int(command.split()[1])-1].pos[1]) 
                        if command.split()[1] == factory[i].id:
                                pass
                        elif factory[int(command.split()[1])-1].pos[0]+1 == factory[i].pos[0] and factory[int(command.split()[1])-1].pos[1] == factory[i].pos[1]:
                            print("If this movement is done robot ",command.split()[1]," and robot ",i+1 ," would collide")  
                            Collision_Bool = True
                            factory[int(command.split()[1])-1].last_pos = factory[int(command.split()[1])-1].pos  

                    elif command.split()[2] == "left":
                        factory[int(command.split()[1])-1].obstacle = (factory[int(command.split()[1])-1].pos[0],factory[int(command.split()[1])-1].pos[1]-1) 
                       
                        if command.split()[1] == factory[i].id:
                                pass
                        elif factory[int(command.split()[1])-1].pos[1]-1 == factory[i].pos[1] and factory[int(command.split()[1])-1].pos[0] == factory[i].pos[0]:
                            print("If this movement is done robot ",command.split()[1]," and robot ",i+1 ," would collide")  
                            Collision_Bool = True
                            factory[int(command.split()[1])-1].last_pos = factory[int(command.split()[1])-1].pos  

                    elif command.split()[2] == "right":
                        factory[int(command.split()[1])-1].obstacle = (factory[int(command.split()[1])-1].pos[0],factory[int(command.split()[1])-1].pos[1]+1)
                        if command.split()[1] == factory[i].id:
                                pass
                        elif factory[int(command.split()[1])-1].pos[1]+1 == factory[i].pos[1] and factory[int(command.split()[1])-1].pos[0] == factory[i].pos[0]:
                            print("If this movement is done robot ",command.split()[1]," and robot ",i+1 ," would collide")  
                            Collision_Bool = True
                            factory[int(command.split()[1])-1].last_pos = factory[int(command.split()[1])-1].pos  

                    else:
                        print("Invalid direction")
                        Collision_Bool = True

                if Collision_Bool == False:
                    factory[int(command.split()[1])-1].last_pos = factory[int(command.split()[1])-1].pos
                    movement = f"mv {command.split()[2]}\n" 
                    os.write(parentw_pipes[int(command.split()[1])-1], movement.encode())
                    reaction = os.read(parentr_pipes[int(command.split()[1])-1],1024).decode()
                    print(reaction.strip())
                    if reaction.strip() == 'OK':
                        posi = "pos\n"
                        os.write(parentw_pipes[int(command.split()[1])-1], posi.encode())
                        rposi = os.read(parentr_pipes[int(command.split()[1])-1],1024).decode()
                        factory[int(command.split()[1])-1].pos = (int(rposi.strip().replace("Position:  (","").split(",")[0]),int(rposi.strip().replace(" ","").split(",")[1].replace(")","")))
                        treasure = 'tr\n'
                        os.write(parentw_pipes[int(command.split()[1])-1], treasure.encode())
                        treaction = os.read(parentr_pipes[int(command.split()[1])-1],1024).decode()

                        if treaction.strip() == 'Treasure.':
                            if factory[int(command.split()[1])-1].pos not in treasure_positions_list:
                                print("Robot ",command.split()[1]," found a treasure!")
                                print("Robot ",command.split()[1] ," status: ",reaction.strip())
                                n_treasures_found += 1
                                TrBool = True
                                if n_treasures == n_treasures_found:
                                    print("All treasures found!")
                                    print("Before exiting...")
                                    for i in range(len(factory)):
                                        ext = "exit\n"
                                        os.write(parentw_pipes[i],ext.encode())
                                        pid_fin, status = os.wait()
                                        if os.WIFEXITED(status):
                                            exreaction = os.read(parentr_pipes[i],1024).decode()   
                                            code = os.WEXITSTATUS(status)
                                            new = exreaction.strip().replace(f"Robot {i+1} is stopped\n","")
                                            print(f"Robot {i+1} with PID:{pid_fin} exits with code: {os.WEXITSTATUS(status)}, {new}.")
                                            factory[int(command.split()[1])-1].last_treasure = False
                                            update_map(factory[int(command.split()[1])-1],TrBool,ObBool,room,s)
                                    print_room(room)
                                    sys.exit(1)
                            else:
                                TrBool = True
                        else:
                            print("Robot ",command.split()[1]," status: ",reaction.strip())

                    elif reaction.strip() == f"Robot {command.split()[1]} cannot move {command.split()[2]}\nKO" :
                        print("Robot "+ str(command.split()[1]) + " cannot move " + command.split()[2],"due to obstacle.")
                        ObBool = True
                    elif reaction.strip() == f"Robot {command.split()[1]} cannot move {command.split()[2]}.\nKO":
                        print("Robot "+ str(command.split()[1]) + " cannot move " + command.split()[2],"due to wall.")
                    elif reaction.strip() == f"Robot {command.split()[1]} cannot move {command.split()[2]} due to battery\nKO" :
                        print("Robot "+ str(command.split()[1]) + " cannot move" + command.split()[2],"due to battery.")

                update_map(factory[int(command.split()[1])-1],TrBool, ObBool, room, s)
                print_room(room)
            else:
                print("Invalid Input:",command.split()[1])
                

        else:
            print("Invalid Input length")
        
if __name__ == '__main__':
    main()        

