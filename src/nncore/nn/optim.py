from typing import Optional
from abc import abstractmethod, ABC

import numpy as np

from numpy.typing import NDArray
from ..utils import zeros


class Optimizer(ABC):
    # References to the parameters of the model
    parameters: list[NDArray]

    @abstractmethod
    def __init__(self, parameters: list[NDArray], *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def apply(self, gradients: list[NDArray]) -> None:
        """
        Given the list of gradfients ∂Loss/∂θ of the loss function w.r.t. the parameters in the
        same order as in the `self.parameters` list, apply the gradients and advance the
        optimizer.
        """
        raise NotImplementedError


class SGD(Optimizer):
    def __init__(
        self,
        parameters: list[NDArray],
        lr: float,
        momentum: float,
        nesterov: bool = False,
        l2_penalty: Optional[float] = None,
        weight_limit: Optional[float] = None,
    ):
        self.lr: float = lr
        self.momentum: float = momentum
        self.nesterov: bool = nesterov
        self.l2_penalty: Optional[float] = l2_penalty
        self.weight_limit: Optional[float] = weight_limit

        self.parameters: list[NDArray] = parameters
        self.velocities: list[NDArray] = [zeros(*param.shape) for param in self.parameters]

    def apply(self, gradients: list[NDArray]):
        for θ, v_θ, grad_θ in zip(self.parameters, self.velocities, gradients):
            # Apply L2 regularization
            if self.l2_penalty:
                grad_θ += self.l2_penalty * θ

            # Update velocities
            v_θ *= self.momentum
            v_θ -= self.lr * grad_θ

            # Update parameters
            if self.nesterov:
                θ += self.momentum * v_θ - self.lr * grad_θ
            else:
                θ += v_θ

            # Apply weight limit normalization
            if self.weight_limit:
                norm = np.linalg.norm(θ, ord=2, axis=0)
                mask = norm > self.weight_limit
                θ *= mask * (self.weight_limit / norm) + (~mask) * 1.0


class Adam(Optimizer):
    def __init__(
        self,
        parameters: list[NDArray],
        lr: float,
        betas: tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        l2_penalty: Optional[float] = None,
        weight_limit: Optional[float] = None,
    ):
        self.lr: float = lr
        self.β1: float = betas[0]
        self.β2: float = betas[1]
        self.eps: float = eps
        self.l2_penalty: Optional[float] = l2_penalty
        self.weight_limit: Optional[float] = weight_limit

        self.t: int = 0
        self.parameters: list[NDArray] = parameters
        self.means: list[NDArray] = [zeros(*param.shape) for param in self.parameters]
        self.variances: list[NDArray] = [zeros(*param.shape) for param in self.parameters]

    def apply(self, gradients: list[NDArray]):
        # Update time step
        self.t += 1

        for θ, m_θ, v_θ, grad_θ in zip(self.parameters, self.means, self.variances, gradients):
            # Apply L2 regularization
            if self.l2_penalty:
                grad_θ += self.l2_penalty * θ

            # Update means
            m_θ *= self.β1
            m_θ += (1 - self.β1) * grad_θ

            # Update variances
            v_θ *= self.β2
            v_θ += (1 - self.β2) * grad_θ**2

            # Compute unbiased estimators
            mhat_θ = m_θ / (1 - self.β1**self.t)
            vhat_θ = v_θ / (1 - self.β2**self.t)

            # Update parameters
            θ -= self.lr * mhat_θ / (self.eps + np.sqrt(vhat_θ))

            # Apply weight limit normalization
            if self.weight_limit:
                norm = np.linalg.norm(θ, ord=2, axis=0)
                mask = norm > self.weight_limit
                θ *= mask * (self.weight_limit / norm) + (~mask) * 1.0


__all__ = [
    "Optimizer",
    "SGD",
    "Adam",
]
