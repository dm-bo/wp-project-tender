def run_checks(checks, checks_enabled, pages, total, red_con, running_config, script_config):
    runtime = {
        "red_con": red_con,
        "running_config": running_config,
        "script_config": script_config,
    }

    return [
        check.run(
            pages,
            total,
            runtime
        )
        for check in checks
        if checks_enabled[check.name]
    ]
