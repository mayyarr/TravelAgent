from agent import run_agent, validate_trip_profile

from agent import extract_trip_profile

goal = """I want to travel to Istanbul for 5 days with a budget of 500 JOD.
 I work on day 2 and day 3 from 9 AM to 4 PM. I like history and coffee.
   Create my trip plan."""

result = run_agent(goal)

'''
print("\n========================")
print("AGENT STEPS")
print("========================")


for step in result["steps"]:

    print("\nStep:", step["step"])

    print("Tool:", step["tool"])

    print("Arguments:", step["arguments"])

    print("Result:", step["result"])


print("\n========================")
print("FINAL ANSWER")
print("========================")

print(result["answer"])
print("\n========================")'''
print(extract_trip_profile(goal))
print("\n========================")
print("\n========================")
x=validate_trip_profile(extract_trip_profile(goal))
print(x)
