# .bashrc

ulimit -s 512
alias l='ls'
alias ll='ls -lh'
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias send='cd /root/data/ttwait/msnlive/send'
alias live='cd /root/data/ttwait/msnlive'
alias pycomm='cd /root/data/ttwait/pycomm'
alias log='cd /root/data/log'
alias pp='ps aux | grep -v grep | grep python '
alias free='free -m'
alias grep='grep --color'
alias terr='tail -f /root/data/log/`date +%m%d%H`.log'
alias err='tail -f /root/data/error.log'
alias tg='terr | grep '
alias lh='ls -lh'
alias ll='ls -l'
alias tg='terr | grep '
alias stop='/root/data/ttwait/vpshelp/stop'
alias fstop='/root/data/ttwait/vpshelp/fstop'
alias load='python /root/data/ttwait/vpshelp/load.py'
alias t='tail -f'
alias update='cd /root/data/ttwait && git stash &&  git pull origin master && . ~/.bashrc'
alias nginxstart='rm -rf /root/data/cache/*; killall -9 nginx; /root/data/nginx/sbin/nginx'
alias super='supervisord -c /root/data/ttwait/vpshelp/supervisord.conf'

export LOGFILEFORMAT='%m%d%H'
export LOGPATH='/root/data/log'
export ACCOUNTHOST='184.82.64.183'
#alias nginxstop='killall -9 nginx'

export PYTHONSTARTUP=~/.pythonrc.py
export PYTHONPATH='/root/data/ttwait/'
export PATH=/usr/local/phantomjs/bin:$PATH;

# Source global definitions
# Source global definitions
if [ -f /etc/bashrc ]; then
        . /etc/bashrc
fi


# User specific aliases and functions
