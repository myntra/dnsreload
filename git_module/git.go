package main

import (
    "bufio"
    "errors"
    "fmt"
    "log"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
    "sync"
)

type Git struct {
    sync.Mutex
    Repo   string
    Branch string
    Path   string
    Filename string
}

type CommitHistory struct {
    ID      string
    ShortID string
    Time    string
    Message string
    Author  string
}

func (g *Git) Pull() error {

    isrepoexist := true
    src, err := os.Stat(g.Path)
    if err != nil {
        isrepoexist = false
    } else if !src.IsDir() {
        return errors.New("Destination is a file")
    }
    if !isrepoexist {
        log.Println("Cloning repo.....", g.Repo, g.Path)
        cmdClone := exec.Command("git", "clone", g.Repo, g.Path)
        err = cmdClone.Start()
        if err != nil {
            return err
        }
        err = cmdClone.Wait()
        if err != nil {
            return err
        }
        if err = os.Chdir(g.Path); err != nil {
            return err
        }
    } else {
        log.Println("Pulling repo .....")
        cmdPull := exec.Command("git", "pull")
        cmdPull.Dir = g.Path
        err = cmdPull.Start()
        if err != nil {
            return err
        }
        err = cmdPull.Wait()
        if err != nil {
            return err
        }
    }
    cmdCheckout := exec.Command("git", "checkout", g.Branch)
    cmdCheckout.Dir = g.Path
    err = cmdCheckout.Start()
    if err != nil {
        return err
    }
    err = cmdCheckout.Wait()
    if err != nil {
        return err
    }
    return nil
}

func (g *Git) GetCommitHistory(fpath string, limit int) ([]*CommitHistory, error) {

    src, err := os.Stat(g.Path)
    if err != nil {
        return nil, err
    } else if !src.IsDir() {
        return nil, errors.New("Destination is a file")
    }
    fpath = filepath.Join(g.Path, fpath)
    cmdChistory := exec.Command("git", "log", "--format=%H:::%h:::%an:::%ar:::%s", fmt.Sprintf("-%d", limit), fpath)
    cmdChistory.Dir = g.Path
    stdout, err := cmdChistory.StdoutPipe()
    if err != nil {
        return nil, err
    }
    err = cmdChistory.Start()
    if err != nil {
        return nil, err
    }
    var commitHistoryRaw []string
    var commitHistory []*CommitHistory
    buff := bufio.NewScanner(stdout)
    for buff.Scan() {
        commitHistoryRaw = append(commitHistoryRaw, buff.Text())
    }
    err = cmdChistory.Wait()
    if err != nil {
        return nil, err
    }

    for _, history := range commitHistoryRaw {
        commitMeta := strings.Split(history, ":::")

        if len(commitMeta) == 5 {
            commitHistory = append(commitHistory, &CommitHistory{ID: commitMeta[0], ShortID: commitMeta[1], Author: commitMeta[2], Time: commitMeta[3], Message: commitMeta[4]})
        } else {
            continue
        }

    }
    return commitHistory, nil
}

func (g *Git) Add(fpath string) error {

    _, err := os.Stat(g.Path)
    if err != nil {
        return err
    }
    log.Println("Adding directory:", filepath.Join(g.Path, fpath))
    cmd_add := exec.Command("git", "add", fpath)
    cmd_add.Dir = g.Path
    err = cmd_add.Start()
    if err != nil {
        return err
    }
    err = cmd_add.Wait()
    if err != nil {
        return err
    }
    return nil
}

func (g *Git) Revert(fpath string) error {
    _, err := os.Stat(g.Path)
    if err != nil {
        return err
    }
    log.Println("reverting directory:", filepath.Join(g.Path, fpath))
    cmd_revert := exec.Command("git", "checkout", fpath)
    cmd_revert.Dir = g.Path
    err = cmd_revert.Start()
    if err != nil {
        return err
    }
    err = cmd_revert.Wait()
    if err != nil {
        return err
    }
    return nil
}

func (g *Git) CommitAndPush(comment string) error {

    src, err := os.Stat(g.Path)
    if err != nil {
        return err
    } else if !src.IsDir() {
        return errors.New("Destination is a file")
    }
    log.Println("Commiting changes ")
    cmd_commit := exec.Command("git", "commit", "-m", comment)
    cmd_commit.Dir = g.Path
    err = cmd_commit.Start()
    if err != nil {
        return err
    }
    err = cmd_commit.Wait()
    if err != nil {
        return err
    }
    log.Println("Pulling latest changes ")
    cmdPull := exec.Command("git", "pull")
    cmdPull.Dir = g.Path
    err = cmdPull.Start()
    if err != nil {
        return err
    }
    err = cmdPull.Wait()
    if err != nil {
        return err
    }
    log.Println("Pushing changes ")
    cmdPush := exec.Command("git", "push", "origin", g.Branch)
    cmdPush.Dir = g.Path
    err = cmdPush.Start()
    if err != nil {
        return err
    }
    err = cmdPush.Wait()
    if err != nil {
        return err
    }
    return nil
}

func (g *Git) GetDiff(fpath string) (string, error) {

    cmdDiff := exec.Command("git", "diff", fpath)
    cmdDiff.Dir = g.Path
    stdout1, err := cmdDiff.StdoutPipe()
    if err != nil {
        return "", err
    }
    err = cmdDiff.Start()
    if err != nil {
        return "", err
    }
    var commitDiffRaw []string
    buff1 := bufio.NewScanner(stdout1)
    for buff1.Scan() {
        commitDiffRaw = append(commitDiffRaw, buff1.Text())
    }
    err = cmdDiff.Wait()
    if err != nil {
        return "", err
    }
    diff_text := strings.Join(commitDiffRaw, "\n")
    return diff_text, nil
}

func (g *Git) IsDiff() (bool, error) {
    if diff, err := g.GetDiff("."); err != nil {
        return false, err
    } else if diff == "" {
        return false, nil
    } else {
        return true, nil
    }
}

