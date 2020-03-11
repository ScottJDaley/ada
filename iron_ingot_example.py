# import the library pulp as p 
import pulp
  
# Create a LP Minimization problem 
prob = pulp.LpProblem('Problem', pulp.LpMinimize)  
  
# Create problem Variables  
x = pulp.LpVariable("iron ore", lowBound = 0)
y = pulp.LpVariable("copper ore", lowBound = 0)
z = pulp.LpVariable("iron ingot", lowBound = 0)
a = pulp.LpVariable("iron ingot recipe", lowBound = 0)
b = pulp.LpVariable("alt iron ingot recipt", lowBound = 0)
  
# Objective Function 
prob += x + y   # Minimize iron and copper ore input

# Constraints: 
prob += a + 2 * b - x == 0   # the iron ore demand from recipes equals the supply
prob += 2 * b - y == 0   # the copper ore demand from recipes equals the supple
prob += a + 5 * b - z == 0   # the iron ingot output is exactly 35/min.
prob += z == 35
  
# Display the problem 
print(prob) 
  
status = prob.solve()   # Solver 
print(pulp.LpStatus[status])   # The solution status 
  
# Printing the final solution 
for v in {x,y,z,a,b}:
    print(v.name + ":", pulp.value(v))
    print(v.name + ":", p.value(v))
