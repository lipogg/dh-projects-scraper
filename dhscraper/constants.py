# Constants
# Regular expression to match URLs
URL_PATTERN = (
    r"(https?://)?"  # matches optional "http://" or "https://"
    r"(www\.)?"  # matches optional "www."            
    r"[-a-zA-Z0-9@:%._\+~#=]{1,256}"  # matches main part of the domain name 
    r"(?:-[\r\n]{0,4}[-a-zA-Z0-9@:%._\+~#=]{1,256})?"  # matches possible line breaks and the continuation of the domain or path, "-" to exclude overmatching in cases such as via\nraganwald.com 
    r"(?:\.[a-zA-Z0-9()]{1,6}\b)+?"  # matches the TLD and possible SLDs, non-greedy quantifier to reduce backtracking
    r"(?:[\r\n]{0,4}[-a-zA-Z0-9()@:%_\+.~#?&//=]{1,256})?"  # matches possible line breaks and the continuation of the path or query params, anchors etc
)
# Regular expression to match the ends of url paths split across lines
PATH_PATTERN = r"[\r\n\s]+([-a-zA-Z0-9@:%._\+~#=/]{1,256})"
