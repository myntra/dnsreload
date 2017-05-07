//go:generate go-bindata -pkg main -o appconfig.go appconfig.toml

package main

import (
    "errors"
    "flag"
)

var (
    appCfg        *AppConfig
    dnsConfigRepo *Git
    invalidIP     error
)

func init() {
    // initalize app config
    appCfg = initializeConfig("appconfig.toml")

    dnsConfigRepo = &Git{
        Repo:   appCfg.Repo,
        Path:   appCfg.Path,
        Branch: appCfg.Branch,
	Filename: appCfg.Filename,
    }

    invalidIP = errors.New("InvalidIP")
}

func main() {
    pullFlag := flag.Bool("pullFlag", false, "Flag for only pull func")
    flag.Parse()
    flagPull := *pullFlag
    dnsConfigRepo.DnsGeneration(flagPull)
}
