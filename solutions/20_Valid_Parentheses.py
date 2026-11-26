class Solution(object):
    def isValid(self, s):
        
        stack = []

        for x in s:
            if x in '({[':
                stack.append(x)
            else:
                if not stack:
                    return False

                top = stack.pop()

                if top == '(':
                    if x != ')':
                        return False
                elif top == '{':
                    if x != '}':
                        return False
                elif top == '[':
                    if x != ']':
                        return False
        
        if len(stack) != 0:
            return False

        return True
