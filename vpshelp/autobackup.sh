#!/bin/bash
 
MyUSER="root"     # 数据库用户名，建议使用root账户或者拥有全局权限的用户名
MyPASS="846266"       # 数据库密码
MyHOST="localhost"          # 数据库服务器
 
# Linux bin paths, change this if it can't be autodetected via which command
MYSQL="$(which mysql)"
MYSQLDUMP="$(which mysqldump)"
CHOWN="$(which chown)"
CHMOD="$(which chmod)"
GZIP="$(which gzip)"
 
# 数据库备份的路径
DEST="/root/data/backup"
 
# Main directory where backup will be stored
MBD="$DEST/mysql"
 
# Get hostname
HOST="$(hostname)"
 
# Get data in dd-mm-yyyy format
NOW="$(date +%d-%m-%Y)"
OLD="$(date -d last-month +%d-%m-%Y)"
 
# File to store current backup file
FILE=""
# Store list of databases
DBS=""
 
# DO NOT BACKUP these databases
IGGY="test mysql information_schema"

rm -rf $MBD
 
[ ! -d $MBD ] && mkdir -p $MBD || :
 
# Only root can access it!
$CHOWN 0.0 -R $DEST
$CHMOD 0600 $DEST
 
# Get all database list first
DBS="$($MYSQL -u $MyUSER -h $MyHOST -p$MyPASS -Bse 'show databases')"
 
cat > ftpcc.sh <<EOF
cd $MBD
ftp -i -n<<!
open pic.caatashoes.com
user ttwait@lx-r.com TTwait846266
cd /public_html/caatashoes/backup
binary
mput *.gz
EOF
 
for db in $DBS
do
    skipdb=-1
    if [ "$IGGY" != "" ];
    then
        for i in $IGGY
        do
            [ "$db" = "$i" ] && skipdb=1 || :
        done
    fi
 
    if [ "$skipdb" = "-1" ] ; then
        FILE="$MBD/$db.$HOST.$NOW.gz"
        echo "delete $db.$HOST.$OLD.gz" >> ftpcc.sh
        # do all inone job in pipe,
        # connect to mysql using mysqldump for select mysql database
        # and pipe it out to gz file in backup dir :)
        $MYSQLDUMP -u $MyUSER -h $MyHOST -p$MyPASS $db | $GZIP -9 > $FILE
    fi
done
 
cat >> ftpcc.sh <<EOF
close
bye
!
EOF
 
sh ftpcc.sh
rm ftpcc.sh
