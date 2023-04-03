# These variables (and by extension this file) was a placeholder for a Discord OAuth integration I was (and still am) planning to do.

discord_base_oauth_url = "https://discord.com/oauth2/authorize"
discord_token_oauth_url = "https://discord.com/api/oauth2/token"
discord_token_revoke_oauth_url = "https://discord.com/api/oauth2/token/revoke"
discord_token_oauth_accept_protocol = "application/x-www-form-urlencoded" # In accordance with the relevant RFCs, the token and token revocation URLs will only accept a content type of application/x-www-form-urlencoded. JSON content is not permitted and will return an error. See: https://discord.com/developers/docs/topics/oauth2
