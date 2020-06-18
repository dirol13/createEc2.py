#!/usr/bin/env python3
try:
	import os
	from flask import Flask,request,render_template
	from flask_httpauth import HTTPBasicAuth
	import boto3
	import os
	import argparse
	import psutil
	import sys
except ImportError:
	os.system("yum install centos-release-scl epel-release python34 python34-devel python34-pip -y")
	os.system("pip3 install -r requirements.txt")

region = "eu-west-1"
ec2 = boto3.resource('ec2')
vpc = "vpc-6440e402"
ami_id="ami-7c491f05"
myName = "key"

parser = argparse.ArgumentParser()
parser.add_argument("-V", "--version", help="show program version", action="store_true")
parser.add_argument("-s", "--service", help="Start web server", action="store_true")
parser.add_argument("-i", "--install", help="Install Python35", action="store_true")
parser.add_argument("-1", "--step1", help="Create key", action="store_true")
parser.add_argument("-2", "--step2", help="Create instance", action="store_true")
parser.add_argument("-3", "--step3", help="Create security group", action="store_true")
args = parser.parse_args()


def create_keypair():
    outfile = open('/root/.ssh/key.pem','w')
    key_pair = ec2.create_key_pair(KeyName=myName)
    KeyPairOut = str(key_pair.KeyMaterial)
    outfile.write(KeyPairOut)
    os.system("chmod 400 ~/.ssh/key.pem")
def create_instance():
    instance = ec2.create_instances(
    ImageId=ami_id,
    MinCount=1,
    MaxCount=1,
    KeyName=myName,
    InstanceType="t2.micro",
    TagSpecifications=[
    {
      'ResourceType': 'instance',
      'Tags': [
        {
          'Key': 'Name',
          'Value': 'key'
        },]
    },
  ],
)
    instance_id=instance[0].instance_Id
    return instance_id
def create_security_group(instance_id):
    ec2 = boto3.resource('ec2')
    sec_group = ec2.create_security_group(
    GroupName=myName, Description='key 80 and 20ports', VpcId=vpc)
    sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='tcp',
    FromPort=80,
    ToPort=80
)
    sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='tcp',
    FromPort=22,
    ToPort=22
)
    ec2.create_tags(Resources=[sec_group.id], Tags=[{'Key': 'Name', 'Value': "key3"}])
    ec2 = boto3.client('ec2')
    ec2.modify_instance_attribute(Groups=['sec_group.id',],InstanceId=instance_id)
    return sec_group.id

def create_ebs_volume():
    mount_point= '/dev/disk1'
    volume = ec2.create_volume(
    AvailabilityZone=region,
    Size=1,
    TagSpecifications=[{'ResourceType': 'volume','Tags': [{'Key': 'Name','Value': myName},]},]
)
    ec2.attach_volume(
    Device='/dev/xvdb',
    InstanceId=instance.id,
    VolumeId=volume.id,)
#    os.popen('echo ";" | sfdisk /dev/xvdb')
#    os.popen('mkfs.ext3 /dev/xvdb')
# Create target Directory if don't exist
    if not os.path.exists(mount_point):
        os.mkdir(mount_point)
        print("Directory " , mount_point ,  " Created ")
    else:
        print("Directory " , mount_point ,  " already exists")
        os.popen('/dev/xvdb mount_point')

def git_clone():
    pass
def start_service():
    auth = HTTPBasicAuth()
    app = Flask(__name__)
    users = {
            "admin": "123",
            "susan": "bye"
    }

    @auth.get_password
    def get_pw(username):
         if username in users:
             return users.get(username)
         return None

    @app.route("/hello",methods=['GET'])
    @auth.login_required
    def hello():
        print (request.args['cpu'])
        pid = os.getpid()
        py = psutil.Process(pid)
        memoryUse = py.memory_info()[0]/2.**30  # memory use in GB...I think
            #    print('memory use:', memoryUse)
        CPU_Pct=str(round(float(os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' ''').readline()),2))
        #print resultsq
        Mem_Usage=str(round(float(memoryUse),2))
    #    print("CPU Usage = " + CPU_Pct)
        return render_template('output.html',
        cpu=CPU_Pct,
        mem=Mem_Usage,
    )
    app.run(debug=True,host='0.0.0.0', port=80)
#Starting
if args.service:
    start_service()
if args.install:
    install_python3()
if args.step1:
    create_keypair()
if args.step2:
    create_instance()
if args.step3:
    create_security_group()
