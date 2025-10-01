@echo off
chcp 65001
title Network Addresses
echo Network addresses for this computer:
echo.
ipconfig | findstr "IPv4"
echo.
echo Use these addresses for other computers to connect
echo Example: http://192.168.1.100:5000
echo.
pause