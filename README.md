
## OAuth flow

Authorization code flow: 

http://sl-server:5000/oauth/authorize?client_id=client-id&state=123456&response_type=code&redirect_uri=http%3A%2F%2Fsl-client%3A7000%2Fcallback&state=dvoQ6Jtv0PV68tBUgUMM035oFiZw57

Implicit flow:
http://sl-server:5000/oauth/authorize?client_id=client-id&state=123456&response_type=token&redirect_uri=http%3A%2F%2Fsl-client%3A7000%2Fcallback&state=dvoQ6Jtv0PV68tBUgUMM035oFiZw57

Exchange the code to get the token with `{code}` replaced by the code obtained in previous step.

http -f -a client-id:client-secret http://localhost:5000/oauth/token grant_type=authorization_code code={code}

Get user info:

http http://localhost:5000/oauth/user_info 'Authorization:Bearer {token}'


## Template structure

base
    single: for login, register page
    default: for all pages when user log ins
        
