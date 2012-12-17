# .bashrc

ulimit -s 512
alias l='ls'
alias ll='ls -lh'
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias send='cd /root/data/ttwiat/msnlive/send'
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
alias stop='/root/data/vpshelp/stop'
alias fstop='/root/data/vpshelp/fstop'
alias load='python /root/data/vpshelp/load.py'
alias t='tail -f'
alias nginxstart='rm -rf /root/data/cache/*; killall -9 nginx; /root/data/nginx/sbin/nginx'
#alias nginxstop='killall -9 nginx'

export PYTHONSTARTUP=~/.pythonrc.py
export PYTHONPATH='/root/data/ttwait/'
export PATH=/usr/local/phantomjs/bin:$PATH;

# Source global definitions
if [ -f /etc/profile ]; then
	. /etc/profile
fi

# User specific aliases and functions
