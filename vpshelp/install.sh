#!/bin/sh
yum remove -y httpd
yum install -y gcc make flex autoconf vixie-cron zlib curl zlib-devel curl-devel bzip2 bzip2-devel ncurses-devel libjpeg-devel libpng-devel libtiff-devel freetype-devel pam-devel libxml libxslt libxslt-devel subversion sed vim* unzip libevent* libgevent* sqlite-devel libtermcap-devel *ssl* which gdb pcre pcre-devel sudo openssh-server zip ftp lrzsz dstat libtool gcc-c++ mysql mysql-server mysql-devel git strace

echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle 
echo 873200 > /proc/sys/net/core/wmem_max
echo 873200 > /proc/sys/net/core/wmem_max
echo "8192  436600  873200" >  /proc/sys/net/ipv4/tcp_wmem
echo "32768  436600  873200" > /proc/sys/net/ipv4/tcp_rmem
echo "786432  1048576 1572864" >  /proc/sys/net/ipv4/tcp_mem
echo 1000 >  /proc/sys/net/core/netdev_max_backlog
echo 256 > /proc/sys/net/core/somaxconn
echo 2048 >  /proc/sys/net/ipv4/tcp_max_syn_backlog


cd

mkdir src
cd src

wget ftp://ftp.cwru.edu/pub/bash/readline-6.2.tar.gz
tar xzvf readline-6.2.tar.gz
cd readline-6.2
./configure
make && make install


cd /root/src
wget http://phantomjs.googlecode.com/files/phantomjs-1.6.1-linux-i686-dynamic.tar.bz2
tar xjvf phantomjs-1.6.1-linux-i686-dynamic.tar.bz2
mv phantomjs-1.6.1-linux-i686-dynamic /usr/local/phantomjs

cd /root/src
wget http://www.python.org/ftp/python/2.6/Python-2.6.tgz
tar xzvf Python-2.6.tgz
cd Python-2.6
./configure
cd Modules

sed -r "s/#readline readline.c -lreadline -ltermcap/readline readline.c -lreadline -ltermcap/"  ./Setup.dist > ./Setup.dist.bak
mv -f ./Setup.dist ./Setup.dist.bak1
mv -f ./Setup.dist.bak ./Setup.dist

cd ~/src/Python-2.6/

make && make install

cd /root/src

wget http://pypi.python.org/packages/2.6/s/setuptools/setuptools-0.6c11-py2.6.egg#md5=bfa92100bd772d5a213eedd356d64086

sh setuptools-0.6c11-py2.6.egg

easy_install-2.6 cython pyquery ClientForm readline supervisor

cd /root/src
wget http://gevent.googlecode.com/files/gevent-1.0b2.tar.gz
tar xzvf gevent-1.0b2.tar.gz 
cd gevent-1.0b2
python2.6 setup.py install

cd /root/src
wget http://sourceforge.net/projects/mysql-python/files/latest/download -O mysql-python.tar.gz
tar xzvf mysql-python.tar.gz
cd MySQL-python*
python2.6 setup.py install

cd

mkdir data
cd data
git clone git://github.com/waitingzeng/ttwait.git

rm -rf ~/.bashrc
ln -s /root/data/ttwait/vpshelp/.bashrc ~/.bashrc
ln -s /root/data/ttwait/vpshelp/supervisord.conf /var/supervisord.conf

. ~/.bashrc

cd /root/data

mkdir log
mkdir backup



cd /root/src
wget http://nginx.org/download/nginx-1.0.12.tar.gz
tar xzvf nginx-1.0.12.tar.gz
cd nginx-1.0.12
./configure --prefix=/root/data/nginx --with-http_sub_module
make && make install
rm -f /root/data/nginx/conf/nginx.conf
ln -s /root/data/ttwait/vpshelp/nginx.conf /root/data/nginx/conf/nginx.conf




cd /root/data/msnlive/data
mkdir sender
cd sender
mkdir zip
cd zip
load -n http://pic.caatashoes.com/account/cache_sender_%s.zip -b 0 -e 36
mv *.txt ../
cd ..
cp *.txt ../


cd /root/data/msnlive/data
mkdir tos
cd tos
mkdir zip
cd zip
load -n http://pic.caatashoes.com/tos/tos_%s.zip -b 0 -e 350
mv *.txt ../
cd ..


cd /root/data/msnsend/data
rm -rf all.txt
mkdir sender
cd sender
load -n http://pic.caatashoes.com/account/cache_sender_%s.zip -b 0 -e 36

(for file in *.txt; do cat $file >> all.txt; echo  $file; done)

rm -rf ../all.txt
mv all.txt ../

crontab -e 
0 * * * * python2.6 /root/start.py


wget http://pypi.python.org/packages/source/r/readline/readline-6.2.2.tar.gz#md5=ad9d4a5a3af37d31daf36ea917b08c77


(for file in base/*; do zip zip/$file.zip $file ; done)

 (for file in *.html; do cat $file ; echo ; echo; done)

cd 
wget http://pic.caatashoes.com/account/accountfails.zip
unzip  accountfails.zip
python2.6 get_fail_account.py
