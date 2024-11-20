import asyncio
import os

from s3e3 import agent


async def main():
    state = agent.IState(
        done=False,
        max_steps=6,
        current_step=1,
        knowledge='',
        system_prompt='',
        messages=[
            {
                "role": "user",
                "content": f"""Query the database at {os.environ['AG3NTS_HQ_URL']}/apidb to find which active datacenters (DC_ID) are managed by employees who are currently on vacation (is_active=0). 
                Send the results to the central system as a database task."""
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

        if '{{FLG:' in state['actions_taken'][-1]['result']:
            break
        state['current_step'] += 1


if __name__ == '__main__':
    # asyncio.run(
    # get_db_structure(
    #     {
    #         "query_type": "show_tables",
    #         'table_name': None,
    #         "_thoughts": "I need to get the structure of the database."
    #     }
    # ))
    asyncio.run(main())
