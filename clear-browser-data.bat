@echo off
echo Clearing browser localStorage data for the application...
echo.
echo Please follow these steps:
echo 1. Open your browser and navigate to the application (http://localhost:5173 or your app URL)
echo 2. Press F12 to open Developer Tools
echo 3. Go to the Console tab
echo 4. Copy and paste this command:
echo.
echo localStorage.removeItem('pothole-reporter-storage'); location.reload();
echo.
echo 5. Press Enter to execute
echo 6. The page will refresh with cleared data
echo.
echo This will remove all existing users from the leaderboard except shoaibshoaib@gmail.com
echo and delete all reports except those from shoaibshoaib@gmail.com
echo.
pause