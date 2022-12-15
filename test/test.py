import ftplib

import paramiko

host='10.122.155.73'
user='root'
pw='1234'

# if __name__ == '__main__':
#     lines = ['합계 780112\n', '-rw-r--r--. 1 aiccta aiccta  10621733 11월  3 17:43 apache-tomcat-8.5.83.tar.gz\n', '-rw-r--r--. 1 aiccta aiccta   9890010 11월  3 17:43 apache-zookeeper-3.5.10-bin.tar.gz\n', '-rw-r--r--. 1 aiccta aiccta  99896916 11월  3 17:43 cmak-3.0.0.5.zip\n', '-rw-r--r--. 1 aiccta aiccta  62283588 11월  3 17:43 kafka_2.12-2.4.0.tgz\n', '-rw-r--r--. 1 aiccta aiccta 277356516 11월  3 17:43 openlogic-openjdk-11.0.8+10-linux-x64.tar.gz\n', '-rw-r--r--. 1 aiccta aiccta 105559173 11월  3 17:44 openlogic-openjdk-8u342-b07-linux-x64.tar.gz\n', '-rw-r--r--. 1 aiccta aiccta 233215067 11월  3 17:44 spark-2.4.6-bin-hadoop2.7.tgz\n']


if __name__ == '__main__':
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.connect(host, username=user, password=pw, port=22)
    print("ssh connection success")

    sftp = ssh.open_sftp()
    sftp.chdir('/home/aiccta/project')
    file_list = sftp.listdir()
    print("file list: {}".format(file_list))
    stdin, stdout, stderr = ssh.exec_command("cd /home/aiccta/project && ls -l")
    lines = stdout.readlines()
    print("lines: {}, type: {}".format(lines, type(lines)))

    # files = {}
    # for line in lines:
    #     print("line: {}".format(line))
    #     file_name = ''
    #     file_ext = ''
    #     file_size = ''
    #     files.append({'file_name': file_name, 'file_ext': file_ext, 'file_size': file_size})
    # print("files: {}".format(files))



    # =================
    # cmd = "sshpass -p '{password}' ssh -oStrictHostKeyChecking=no {username}@{host} -p {port} 'ls -l --full-time {path}'".format(
    #     username=username, password=password, host=host, port=port, path=path)
    # ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # err = ret.stderr.decode('utf-8')
    # out = ret.stdout.decode('utf-8')
    #
    # if err:
    #     return err, []
    #
    # files = []
    # res = out.split('\n')
    # for r in res:
    #     t = r.split()
    #     if len(t) > 8 and 'd' not in t[0] and 'l' not in t[0]:
    #         file_name = t[8]
    #         file_size = t[4]
    #         file_mtime = " ".join(t[5:7])
    #         files.append({'name': file_name, 'size': file_size, 'mtime': file_mtime})


# if __name__ == '__main__':
#     with ftplib.FTP() as ftp:
#         ftp.connect(host=host, port=21)
#         ftp.encoding = 'utf-8'
#         s = ftp.login(user=user, passwd=pw)
#         print("ftp connection success")
#
#         ftp.cwd('/home/aiccta/project')
#         list = ftp.nlst()
#         print("dir list: {}".format(list))

