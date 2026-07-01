def compute_srd_branch_gate_weight(use_branch_gate, iteration, start_iter=0, ramp_iters=0):
    if not use_branch_gate:
        return 0.0
    start_iter = max(0, int(start_iter))
    ramp_iters = max(0, int(ramp_iters))
    iteration = max(0, int(iteration))
    if iteration < start_iter:
        return 0.0
    if ramp_iters == 0:
        return 1.0
    return min(1.0, max(0.0, float(iteration - start_iter) / float(ramp_iters)))


def compute_srd_render_gate_weight(
    use_branch_gate,
    iteration,
    branch_gate_start_iter=0,
    branch_gate_ramp_iters=0,
    render_gate_start_iter=-1,
    render_gate_ramp_iters=-1,
):
    if int(render_gate_start_iter) < 0:
        render_gate_start_iter = branch_gate_start_iter
    if int(render_gate_ramp_iters) < 0:
        render_gate_ramp_iters = branch_gate_ramp_iters
    return compute_srd_branch_gate_weight(
        use_branch_gate=use_branch_gate,
        iteration=iteration,
        start_iter=render_gate_start_iter,
        ramp_iters=render_gate_ramp_iters,
    )
