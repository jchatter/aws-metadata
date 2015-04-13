#!/usr/bin/python
#-*- Mode: python -*-
import json
from runcmd import runcmd
from pprint import pprint
from pyhop import pyhop

################################################################################
# Takes each IP, parses desired metadata, and updates description/device tags
################################################################################
def AWS_Instances_Metadata(client, device, json_data):
    data = json.loads(json_data)
    #####################################################
    # Parse the JSON file and print the desired metadata
    #####################################################
    # Device name
    if not data["Reservations"]:
        return

    inst = data["Reservations"][0]["Instances"][0]
    tags = {tag["Key"]:tag["Value"]
       for tag in inst["Tags"]}
    print "\ntags : %s" % tags
    if "aws:autoscaling:groupName" in tags:
        print "Name : " + tags["aws:autoscaling:groupName"]          
        devicename = tags["aws:autoscaling:groupName"]
    elif "Name" in tags:
        print "Name:"  + tags["Name"]
        devicename = tags["Name"]
    else:  
        return

    labels = {'LaunchTime'  : 'Launch Time', 
              'InstanceId'  : 'Instance ID :' ,
              'ImageId'     : 'Image ID :',
              'Architecture': 'Architecture :', 
              'InstanceType': 'Size :',} 
    for key, label in labels.items():
	print "\n%s: %s" % (label, inst[key])  

    # Security group
    print "\nSecurity Group :",
    print ", ".join(inst["SecurityGroups"][i]["GroupName"]
                    for i in range(len(inst["SecurityGroups"])))

    # Tags(s)
    print "\nTags(s) :",
    print ", ".join(inst["Tags"][i]["Value"]
                    for i in range(len(inst["Tags"])))
    #print inst["Tags"]
    tags1 = inst["Tags"]
    key_value = [(item['Key'], item['Value']) for item in tags1]

    # State
    print "\nState : " + inst["State"]["Name"]

    ########################################################
    # Updates Description for each device that has metadata
    ########################################################
    comment = ("Device Name: " + devicename + "\n" +
               "Instance ID: " + inst["InstanceId"] + "\n" + "AMI ID: " +
               inst["ImageId"] + "\n" + "Launch Time: " + inst["LaunchTime"] +
               "\n" + "Architecture: " + inst["Architecture"] + "\n" +
               "Instance Size: " + inst["InstanceType"] + "\n" + "Zone: " +
               inst["Placement"]["AvailabilityZone"] + "\n" +
               "Security Group(s): " + inst["SecurityGroups"][0]["GroupName"] +
               "\n")
    client.update_device({"oid": device.oid, "comment": comment})
    ########################################################
    # Updates Device Tags for each device that has metadata 
    ########################################################  
    object_ids = [device.oid]
    a = [inst["SecurityGroups"][0]["GroupName"], devicename,
         inst["InstanceId"], inst["ImageId"], inst["Architecture"], 
         inst["InstanceType"], inst["Placement"]["AvailabilityZone"]]
    for key, value in key_value:
        a.append(key + " : " + value) 
    for value in a:
	client.device_tag_add(value, object_ids)
    #######################################################################
    # Runs Function for each IP found to update Description and Device Tags
    ####################################################################### 

def main():
    ################################
    #Searches for Active Devices  
    ################################
    # max number of devices to poll
    max_dev = 1000
    c = pyhop.make_client()
    #result = c.search_devices_by_activity(-180000,0, "activity" )
    result = c.get_active_devices(0,max_dev,-1800000, 0) 
    for d in result.devices:
       if d.ipaddr4 != None:
          print d.ipaddr4
          json_data = runcmd('aws ec2 describe-instances --filter \''+
                           '[{"Name":"private-ip-address","Values":["' +
                           d.ipaddr4 + '"]}]\'')    
          AWS_Instances_Metadata(c, d, json_data)
    ############################################################################
    # For each of the devices listed, the metadata is gathered using the EC2 API
    ############################################################################
    # Command from EC2 API: 
    #    aws ec2 describe-instances 
    #     --filter '{"name":"private-ip-address","values":"10.0.0.147"}'
    ############################################################################

if __name__ == "__main__":
    main()
