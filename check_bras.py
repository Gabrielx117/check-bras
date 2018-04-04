#!/usr/bin/env python3
#coding=utf-8

import pexpect,sys,re,time,threading,os,json

result={}
Debug = 0
with open (sys.path[0] + "/braslist.json") as b :
    info=json.load(b)

bras=info['bras']
username=info['username']
passwd=info['passwd']

class Bras():
    """docstring for ClassName"""
    def __init__(self, index,hostip, model):
        self.index = index
        self.model = model
        self.hostip = hostip
        if self.model == 'redback':
            self.login = 'ogin: '
            self.cmd= ('context pppoe','show ip pool cont sum','exit')
        elif self.model == 'me60':
            self.cmd= ('display ip pool','q','quit')
            self.login='name:'
    def connect(self):
        loginprompt = '[$#>]'
        self.child = pexpect.spawn('telnet %s' % self.hostip)
        index = self.child.expect([self.login, "(?i)Unknown host", pexpect.EOF, pexpect.TIMEOUT])
        if (index == 0) :
            self.child.sendline(username)
            index = self.child.expect(["[pP]assword", pexpect.EOF, pexpect.TIMEOUT])
            self.child.sendline(passwd)
            self.child.expect(loginprompt)
            if (index == 0):
                return True
            else:
                print ("telnet login failed, due to TIMEOUT or EOF")
                self.child.close(force=True)
                return False
        else:
            print ("telnet login failed, due to TIMEOUT or EOF")
            self.child.close(force=True)
            return False
    def get_info(self):
        if self.connect():
            for c in self.cmd:
                self.child.sendline(c)
            index = self.child.expect(pexpect.EOF)
            if (index == 0):
                self.content = self.child.before.decode().split('\r') #由于pexpect返回为bytes类型,python3中需要转码为str类型
                self.child.close(force=True)
                return True
        else:
            print ("get info fail. please check!")
            sys.exit(1)
    def filter_info(self):
        self.get_info()
        if self.model == "redback":
            for line in  self.content:
                if "in use" in line:
                    l = line.strip().split()
                    self.result = {self.index:{'used ip':l[0],'free ip':l[3]} }
        elif self.model == "me60":
            if 'Used' in self.content[-11]:
                cont=re.split(r'\s+:?', self.content[-11].strip())
            else:
                cont=re.split(r'\s+:?', self.content[-12].strip())
            self.result = {self.index:{'used ip':cont[1],'free ip':cont[3]} }
        else:
            print ("filter info fail. please check!")
            sys.exit(1)

        if self.result is not None:
            return self.result

class __redirection__:
    #redirect print to stdout & outfile
    def __init__(self):
        #get sys.stdout
        self.buff=''
        self.__console__=sys.stdout

    def write(self, output_stream):
        self.buff+=output_stream

    def to_console(self):
        sys.stdout=self.__console__
        print (self.buff)

    def to_file(self, file_path):
        f=open(file_path,'w')
        sys.stdout=f
        print (self.buff)
        f.close()

    def flush(self):
        self.buff=''

    def reset(self):
        sys.stdout=self.__console__

def run(index,hostip,model):
    ins=Bras(index,hostip,model)
    record=ins.filter_info()
    result.update(record)

def main():
    start= time.time()
    thread=[]
    for i in bras.keys():
        '''每个实例建立一个线程'''
        t= threading.Thread(target=run,args=(i,bras[i].get('ip'),bras[i].get('model')))
        thread.append(t)
        t.start()

    for i in range(len(thread)):
        '''等待线程结束'''
        thread[i].join()

    print ('index\tUsed IP\tFree IP')
    for key in sorted(result.keys()):
        print ('%s\t%s\t%s' %(key,result[key]['used ip'],result[key]['free ip']))
    print ("Elapsed Time: %s" % (time.time() - start))

if __name__ == '__main__':
    user=os.getlogin()
    date=time.strftime('%Y%m%d%H%M%S')
    outlog='/var/log/bras/%s_%s'%(user,date)
    if user == 'root':
        log='/root/%s' %date
    else:
        log='/home/%s/%s' %(user,date)
    r_obj=__redirection__()
    sys.stdout=r_obj
    main()
    r_obj.to_console()
    r_obj.to_file(outlog)
    r_obj.to_file(log)
    r_obj.flush()
    r_obj.reset()

