#!/bin/bash
### BEGIN INIT INFO
# Title: fulcrum.sh
# Provides: fulcrum
# Required-Start: $syslog
# Required-Stop: $syslog
# Should-Start:
# Should-Stop:
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Fill dev_random with entropy from random.org
# Description: Provide enough entropy to keep dev_random available as long
# as Random.Org API or HTTP quota is ok
# License: GNU GENERAL PUBLIC LICENSE Version 2
# Author: Ruben Carlo Benante <rcb@beco.cc>
# Date: 2017-03-18
# Version: 20170318.024211
# Usage: sh fulcrum.sh
# Notes: This is a start script for a python script at /usr/local/bin/fulcrum
# bash_version: GNU bash, version 4.2.37(1)-release (x86_64-pc-linux-gnu)
### END INIT INFO

# **************************************************************************
# * (C)opyright 2017         by Ruben Carlo Benante                        *
# *                                                                        *
# * This program is free software; you can redistribute it and/or modify   *
# *  it under the terms of the GNU General Public License as published by  *
# *  the Free Software Foundation version 2 of the License.                *
# *                                                                        *
# * This program is distributed in the hope that it will be useful,        *
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *  GNU General Public License for more details.                          *
# *                                                                        *
# * You should have received a copy of the GNU General Public License      *
# *  along with this program; if not, write to the                         *
# *  Free Software Foundation, Inc.,                                       *
# *  59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
# *                                                                        *
# * Contact author at:                                                     *
# *  Ruben Carlo Benante                                                   *
# *  rcb@beco.cc                                                           *
# **************************************************************************

# The help
Help()
{
    cat << EOF
    fulcrum - Fill dev_random with entropy from random.org
    Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status} | [-h|-V|-v]
  
    Options:
      -h, --help       Show this help.
      -V, --version    Show version.
      -v, --verbose    Turn verbose mode on.
    Exit status:
       0, if ok.
       1, some error occurred.
  
    Todo:
            Long options not implemented yet.
  
    Author:
            Written by Ruben Carlo Benante <rcb@beco.cc>  

EOF
    exit 1
}

# Another usage function example
# usage() { echo "Usage: $0 [-h | -c] | [-a n -i m], being n>m" 1>&2; exit 1; }

# The Copyright and Version information
Copyr()
{
    echo 'fulcrum - 20170318.024211'
    echo
    echo 'Copyright (C) 2017 Ruben Carlo Benante <rcb@beco.cc>, GNU GPL version 2'
    echo '<http://gnu.org/licenses/gpl.html>. This  is  free  software:  you are free to change and'
    echo 'redistribute it. There is NO WARRANTY, to the extent permitted by law. USE IT AS IT IS. The author'
    echo 'takes no responsability to any damage this software may inflige in your data.'
    echo
    exit 1
}

# The start function
do_start()
{
    log_daemon_msg "Starting system $DAEMON_NAME daemon"
    start-stop-daemon --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas $DAEMON -- $DAEMON_OPTS
    log_end_msg $?
}

# The stop function
do_stop()
{
    log_daemon_msg "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --retry 10
    log_end_msg $?
}

# The Main function
main()
{
    verbose=0
    #getopt example with switch/case
    case "$1" in
        -h)
            Help
            ;;
        -V)
            Copyr
            ;;
        -v)
            verbose=1
            ;;
        start|stop)
            do_${1}
            ;;
        restart|reload|force-reload)
            do_stop
            do_start
            ;;
        status)
            status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
            ;;
        *)
            Help
            ;;
    esac
}

# Example of a function
notready()
{
    exit 0


    while [ 1 ] ; do
        entropy=`cat /proc/sys/kernel/random/entropy_avail`
        echo "Entropy available: $entropy"

        if [ "$entropy" -gt 900 ]; then
            echo "It is ok. Sleeping for a while"
            sleep 2
        else
            echo "It is low. Running"
            password=`openssl rand -base64 48`
            quota=`curl 'https://www.random.org/quota/?format=plain'`
            echo "Your quota: $quota"
            if [ "$quota" -le 4000 ]; then
                echo "Not enough quota. Consider the paying service of www.random.org"
                echo "Skipping"
                continue
            fi
            echo "Quota is enough. Grabbing some random numbers"
            randomorg="https://www.random.org/integers/?num=1000&min=0&max=1000000000&col=1&base=10&format=plain&rnd=new"
            echo DEBUG: using previous tmp file
            #rand=`curl $randomorg`
            #frand="$(mktemp)"
            #echo $rand | openssl enc -aes-256-cbc -pass pass:$password > $frand
            frand=/tmp/tmp.zSK5s14RPS
            sudo rngd -f -t 1 -r $frand
        fi
        sleep 1
    done

    entropy=`cat /proc/sys/kernel/random/entropy_avail`
    echo "Entropy available after running: $entropy"


    exit 1
  
    if [ -z "$max" ] || [ -z "$min" ]; then
        Help
    fi
    if [ "$max" -le "$min" ]; then
        echo "Restriction: Max > Min"
        exit 1
    fi
  
    echo Starting fulcrum.sh script, by beco, version 20170318.024211...
  
    echo Verbose level: $verbose
  
    #for example
    echo list of files:
    for i in $( ls ); do
        echo item: $i
    done
    echo
  
    #echo read from stdin
    backupfile=/home/$USER/$(date +%Y%m%d)-documents-backup.tgz
    echo Issuing command: tar -cZf $backupfile /home/$USER/Documents
    read Opt
    echo Your answer: $Opt
    if [ "$Opt" = "y" ]; then
        echo Just kidding\!
    else
        echo Thanks god I dont need to work today\!
    fi
    
     #while counter example
    COUNTER=2
    while [  "$COUNTER" -gt 0 ]; do
        echo The counter is $COUNTER seconds
        let COUNTER=COUNTER-1
        sleep 1 # wait 1 second
    done
    
    #Menu
    if [ -z "$www" ]; then
        echo Please chose an option number:
        OPTIONS="Google Yahoo Facebook Quit"
        select opt in $OPTIONS; do
            if [ "$opt" = "Quit" ]; then
                echo Please stop the world, I wanna get out.
                www=""
                break
            elif [ "$opt" = "Google" ]; then
                echo Make a new World
                www="www.google.com"
                break
            elif [ "$opt" = "Yahoo" ]; then
                echo 'No way! Chose another!'
            elif [ "$opt" = "Facebook" ]; then
                echo Save the World
                www="facebook.com"
                break
            else
                echo "Bad server, no donut for you"
            fi
        done
    fi
    
    echo Pinging $www
    ping -c1 $www 2>/dev/null  1>/dev/null
    pingstatus=$?
    if [[ "$pingstatus" -ne "0" ]]; then
        echo $www down
        beep
    else
        echo ping ok
    fi
    
    echo Bye
}

#Calling main with all args
DIR=/usr/local/bin/fulcrum
DAEMON=$DIR/fulcrum.py
DAEMON_NAME=fulcrum

# Add any command line options for your daemon here
DAEMON_OPTS=""

# This next line determines what user the script runs as.
DAEMON_USER=root

# The process ID of the script when it runs is stored here:
PIDFILE=/var/run/$DAEMON_NAME.pid

. /lib/lsb/init-functions
main $*
exit 0

#/* -------------------------------------------------------------------------- */
#/* vi: set ai et ts=4 sw=4 tw=0 wm=0 fo=croql : SHELL config for Vim modeline */
#/* Template by Dr. Beco <rcb at beco dot cc> Version 20160714.124739          */

