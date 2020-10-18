import numpy as np
from collections import Counter, namedtuple


class LR():
    def __init__(self, lr=0.01, steps=5000):
        self.lr = lr
        self.steps = steps

    def s(self, z):
        return 1 / (1 + np.exp(-z))

    def fit(self, X, y):
        X = np.hstack((np.ones((X.shape[0], 1)), X))
        self.coefs = np.zeros(X.shape[1])  # weights

        for _ in range(self.steps):
            h = self.s(np.dot(X, self.coefs))
            self.coefs -= self.lr * \
                np.dot(X.T, (h - y)) / y.size  # gradient  step

    def predict(self, X):
        X = np.hstack((np.ones((X.shape[0], 1)), X))
        return self.s(np.dot(X, self.coefs)).round()


class KNN():
    def __init__(self, nn=5):
        self.nn = nn

    def dists(self, X):
        num_test = X.shape[0]
        num_train = self.X.shape[0]

        t = np.dot(X, self.X.T)
        dists = np.sqrt(-2 * t + np.square(self.X).sum(1) +
                        np.matrix(np.square(X).sum(1)).T)
        return dists

    def fit(self, X, y):  # no direct procedure, just search
        self.X = X
        self.y = y

    def predict(self, X):
        dists = self.dists(X)
        preds = np.zeros(dists.shape[0])

        for i in range(dists.shape[0]):
            labels = self.y[np.argsort(dists[i, :])].flatten()
            top_nn_y = labels[:self.nn]
            preds[i] = Counter(top_nn_y).most_common(1)[0][0]
        return preds

class Node():
    def __init__(self, predicted_class):
        self.predicted_class = predicted_class
        self.feature_index = 0
        self.threshold = 0
        self.left = None
        self.right = None

class DTC():

    def __init__(self, max_depth=1, rf=False):
        self.max_depth = max_depth
        self.rf = rf

    def fit(self, X, y, max_features=None):
        self.n_classes_ = len(set(y))
        if not self.rf:
            n_features_ = X.shape[1]
        else:
            ind = np.random.choice(X.shape[0], X.shape[0])
            X, y = X[tuple([ind])], y[tuple([ind])]
            if max_features is None:
                n_features_ = np.sqrt(X.shape[1]).astype(int)
            else:
                n_features_ = max_features
        self.features_ = np.sort(np.random.choice(X.shape[1], n_features_,
                                                  replace=False))
        self.tree_ = self._grow_tree(X, y)

    def predict(self, X):
        return [self._predict(inputs) for inputs in X]

    def _best_split(self, X, y):
        m = y.size
        if m <= 1:
            return None, None
        num_parent = [np.sum(y == c) for c in range(self.n_classes_)]
        best_gini = 1.0 - sum((n / m) ** 2 for n in num_parent)
        best_idx, best_thr = None, None
        for idx in self.features_:
            thresholds, classes = zip(*sorted(zip(X[:, idx], y)))
            num_left = [0] * self.n_classes_
            num_right = num_parent.copy()
            for i in range(1, m):
                c = classes[i - 1]
                num_left[c] += 1
                num_right[c] -= 1
                gini_left = 1.0 - sum(
                    (num_left[x] / i) ** 2 for x in range(self.n_classes_)
                )
                gini_right = 1.0 - sum(
                    (num_right[x] / (m - i)) ** 2 for x in range(self.n_classes_)
                )
                gini = (i * gini_left + (m - i) * gini_right) / m
                if thresholds[i] == thresholds[i - 1]:
                    continue
                if gini < best_gini:
                    best_gini = gini
                    best_idx = idx
                    best_thr = (thresholds[i] + thresholds[i - 1]) / 2
        return best_idx, best_thr

    def _grow_tree(self, X, y, depth=0):
        num_samples_per_class = [np.sum(y == i)
                                 for i in range(self.n_classes_)]
        predicted_class = np.argmax(num_samples_per_class)
        node = Node(predicted_class=predicted_class)
        if depth < self.max_depth:
            idx, thr = self._best_split(X, y)
            if idx is not None:
                indices_left = X[:, idx] < thr
                X_left, y_left = X[indices_left], y[indices_left]
                X_right, y_right = X[~indices_left], y[~indices_left]
                node.feature_index = idx
                node.threshold = thr
                node.left = self._grow_tree(X_left, y_left, depth + 1)
                node.right = self._grow_tree(X_right, y_right, depth + 1)
        return node

    def _predict(self, inputs):
        node = self.tree_
        while node.left:
            if inputs[node.feature_index] < node.threshold:
                node = node.left
            else:
                node = node.right
        return node.predicted_class



class RFC():
    def __init__(self, max_depth=5, n_trees=10):
        self.max_depth = max_depth
        self.n_trees = n_trees
        self.trees = [None] * n_trees

    def fit(self, X, y):
        for i in range(self.n_trees):
            
            idx = np.random.choice(X.shape[0], X.shape[0])
            X, y = X[tuple([idx])], y[tuple([idx])] # bootstrap
            
            n_features = np.sqrt(X.shape[1]).astype(int)
            X = X[:, np.random.choice(X.shape[1], n_features, replace=False)] #crf
            
            self.trees[i] = DTC(self.max_depth)
            self.trees[i].fit(X, y)

    def predict(self, X):
        raw_preds = np.zeros((self.n_trees, X.shape[0]))
        ans = np.empty(X.shape[0])
        for i in range(self.n_trees):
            raw_preds[i] = self.trees[i].predict(X)
        for i in range(len(ans)):
            ans[i] = Counter(raw_preds[:, i]).most_common(1)[0][0]
        return ans.astype(int)
