import numpy as np
import pyflann
from gym.spaces import Box
from ddpg import agent


class WolpertingerAgent(agent.DDPGAgent):

    def __init__(self, env, max_actions=1e6, max_to_k_ration = 0.1):
        super().__init__(env)
        assert isinstance(env.action_space, Box), "action space must be continuous"
        self.actions = self.init_action_space(env, max_actions)
        print(self.actions.shape)
        print(self.actions)
        exit()

        self.k_nearest_neighbors = int(max_to_k_ration*max_actions)
        print('wolpertinger agent init')
        print('max actions = ', max_actions)
        print('k nearest neighbors =', self.k_nearest_neighbors)
        # init flann
        self.actions.shape = (len(self.actions), self.action_space_size)
        self.flann = pyflann.FLANN()
        params = self.flann.build_index(self.actions, algorithm='kdtree')
        print('flann init with params->', params)

    def get_name(self):
        return 'Wolp_v1_k' + str(self.k_nearest_neighbors) + '_' + super().get_name()

    def init_action_space(self, env, max_actions, equal_actions_in_each_dim = False):
        print(env)
        print(max_actions)
        space = env.action_space
        low = space.low
        high = space.high
        print(low, high)
        dims = len(low)
        print(max_actions**(1/dims))



    def act(self, state):
        proto_action = super().act(state)
        if self.k_nearest_neighbors <= 1:
            return proto_action

        if len(proto_action) > 1:
            return 0
            res = np.array([])
            for i in range(len(proto_action)):
                res = np.append(res, self.wolp_action(state[i], proto_action[i]))
            res.shape = (len(res), 1)
            return res
        else:
            return self.wolp_action(state, proto_action)

    def wolp_action(self, state, proto_action):
        debug = False
        actions = self.nearest_neighbors(proto_action)[0]
        if debug:
            print('--\nproto action', proto_action, 'state', state)
        states = np.tile(state, [len(actions), 1])
        actions_evaluation = self.critic_net.evaluate_critic(states, actions)
        if debug:
            print('action evalueations', actions_evaluation.shape)
        if debug:
            for i in range(len(actions)):
                print(actions[i], 'v', actions_evaluation[i])

        max_index = np.argmax(actions_evaluation)
        max = actions_evaluation[max_index]
        if debug:
            print('max', max, '->', max_index)
        if debug:
            print('result action', actions[max_index])
        # if debug:
        #     exit()
        return actions[max_index]

    def nearest_neighbors(self, proto_action):
        results, dists = self.flann.nn_index(
            proto_action, self.k_nearest_neighbors)  # checks=params["checks"]
        return self.actions[results]
