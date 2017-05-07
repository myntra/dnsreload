package main

import (
    "log"
    "io/ioutil"
    "github.com/BurntSushi/toml"
)


type AppConfig struct {
    Repo              string        `toml:"repo"`
    Path              string        `toml:"path"`
    Branch            string        `toml:"branch"`
    Filename          string         `toml:"filename"`
}

// InitializeConfig method reads config from yaml file
func initializeConfig(path string) *AppConfig {

    var appCfg AppConfig

    data, err := ioutil.ReadFile(path)
    if err != nil {
        panic("Config file missing or unreadable " + err.Error())
    }

    // Read data from toml file
    if err := toml.Unmarshal(data, &appCfg); err != nil {
        panic("Unable to decode config file " + err.Error())
    }

    log.Println("Config:", &appCfg)

    return &appCfg

}
