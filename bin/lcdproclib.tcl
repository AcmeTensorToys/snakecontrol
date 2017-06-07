namespace eval ::lcdproclib {
	variable version 0.0.1
}

proc ::lcdproclib::cmd {sid cmd} {
  send -i ${sid} "${cmd}\n"
  while { true } {
    expect {
      -i ${sid} -re "^[lindex [split "${cmd}"] 0]\[^\n\]*\r\n" {
         while { true } {
           expect {
             -i ${sid} -re "^success\[^\n\]*\n" { return }
             -i ${sid} -re "^\r\n" { }
             -i ${sid} -re "^listen .*\n" {}
             -i ${sid} -re "^ignore .*\n" {}
             timeout { error "LCD protocol failure while waiting for success?" } 
           }
         }
       }
      -i ${sid} -re "^listen .*\n" {}
      -i ${sid} -re "^ignore .*\n" {}
      timeout { error "LCD protocol failure while waiting for echo?" } 
    }
  }
}

proc ::lcdproclib::spawnlcd {host port} {
  spawn socat STDIO "TCP:${host}:${port}"
  send -i ${spawn_id} "hello\n"
  expect {
    -i ${spawn_id} -re "^hello\r\nconnect .*\r\n" { return ${spawn_id} }
    timeout { error "LCD protocol failure while sending hello?" } 
  }
}

package provide lcdproclib $::lcdproclib::version
