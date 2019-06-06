
## OAuth flow

Get the code: 

http://localhost:5000/oauth/authorize?client_id=client-id&state=123456&response_type=code

Exchange the code to get the token with `{code}` replaced by the code obtained in previous step.

http -f -a client-id:client-secret http://localhost:5000/oauth/token grant_type=authorization_code code={code}

Get user info:

http http://localhost:5000/oauth/user_info 'Authorization:Bearer {token}'