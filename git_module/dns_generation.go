package main

import (
    "fmt"
    "log"
    "os"
    "time"
)

func (dnsConfigRepo *Git) DnsGeneration (onlyPull bool) error {
    dnsConfigRepo.Lock()
    defer dnsConfigRepo.Unlock()
    // Pull and update the repo
    if onlyPull {
	fmt.Println("Flag is true")
        if err := dnsConfigRepo.Pull(); err != nil {
            return err
        }
	return nil
    }

    if err := dnsConfigRepo.Pull(); err != nil {
         return err
     }
    // check for diff in the repo
    isDiff, err := dnsConfigRepo.IsDiff()
   
    if err != nil {
        return err
    }
    // commit and push only if there are changes
    if isDiff {
        // git add <repo-directory>        
        if err = dnsConfigRepo.Add(dnsConfigRepo.Filename); err != nil {
                return err
   	}
        hostname, _ := os.Hostname()
        commitMessage := fmt.Sprintf("Cron update : %s, hostname: %s, PID: %d", time.Now().String(), hostname, os.Getpid())
        // commit and push
        if err = dnsConfigRepo.CommitAndPush(commitMessage); err != nil {
            return err
        }
        commitHist, err := dnsConfigRepo.GetCommitHistory(".", 1)
        if err != nil {
            return err
        }

        if len(commitHist) > 0 {
            log.Println("Pushed with commit ID:", commitHist[0].ID, "\n")
        } else {
            log.Println("Pushed with commit message:\"", commitMessage, "\"", "\n")
        }
        
    } else {
        log.Println("No diff found. Returning\n")
    }
    return nil
}
