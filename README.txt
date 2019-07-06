//README.txtStudent ID: z5129269Name: Mingyue WeiInstallation Guide

For running the project, please following the steps below to compile and deploy
1. unzip two zips, one is called server.zip and the other is called client.zip
2. Server.zip contains ass2.py, data.json and requirement.txt
3. Client.zip contains two folders.
   -one is static which has jquery.json-viewer.css, jquery.json-viewer.js and loading.gif
   -the other is templates which has js_client.html
4. Set up the following structure: 
   - a project named App(this name can be anything)

   — App|-client———|-templates——-js_client.html
        |          |
	|	   |
        |          |-static—————|-jquery.json-viewer.css
        |                       |
        |                       |-jquery.json-viewer.js
	|                       |
        |                       |-loading.gif
        |            
        |-server——-|—ass2.py    
        |          |      
        |          |-data.json 
        |          |
        |          |-requirement.txt

5. Requirement.txt contains all the requirements the project need, please install them before running the project
6. Data.json is Data Source 2 - Australian LGA postcode mappings
7. Js_client.html is frontend
8. Static folder contains some css, js and picture the frontend need
9. Run the file ass2.py in the pycharm
10. Go to http://localhost:5000/ to test the project

      