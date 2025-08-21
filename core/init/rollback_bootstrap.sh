#!/bin/bash
echo "[rollback] Disabling bootstrap service..." | tee -a ~/BlackStack/WachterEID/logs/bootstrap_rollback.log
sudo systemctl stop wachter-bootstrap.service
sudo systemctl disable wachter-bootstrap.service
echo "[rollback] Reverting to pre-bootstrap state complete." | tee -a ~/BlackStack/WachterEID/logs/bootstrap_rollback.log
