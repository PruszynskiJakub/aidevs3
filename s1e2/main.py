import asyncio

from s1e2 import agent


async def main():
    state = agent.IState(
        done=False,
        max_steps=4,
        current_step=1,
        knowledge='',
        system_prompt='',
        messages=[
            {
                "role": "user",
                "content": """Please get the secret password from the robots in the game as the being. 
                All required instructions you gonna find in the file named instr.txt. 
                It contains details about communication protocol and secret knowledge required to deceive robots as the being.
                Good luck!"""
            }
        ],
        actions_taken=[],
    )

    while state['done'] == False and state['current_step'] <= state['max_steps']:
        print(f"Current step: {state['current_step']}")
        await agent.plan(state)
        await agent.decide(state)
        await agent.describe(state)
        await agent.execute(state)
        state['current_step'] += 1


if __name__ == '__main__':
    asyncio.run(main())
