import beaker as bk
import pyteal as pt


class MyState:

    total_votos_A = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64, default=pt.Int(0)
    )


    total_votos_B = bk.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
    )

    total_votantes = bk.GlobalStateValue(pt.TealType.uint64)

    voto_realizado = bk.LocalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="0 = no voto in, 1 = ya voto",
    )

app = (
    bk.Application("HelloWorld", state=MyState())
    .apply(bk.unconditional_create_approval, initialize_global_state=True)
    .apply(bk.unconditional_opt_in_approval, initialize_local_state=True)
)

@app.external
def hello(name: pt.abi.String,*, output: pt.abi.String) -> pt.Expr:
    return output.set(pt.Bytes("Hola maestro"))


@app.external()
def registrar_voto(voto: pt.abi.String, *, output: pt.abi.String) -> pt.Expr:
    """Permite votar por uno de los candidatos"""
    return pt.Seq(
        pt.Assert(
            app.state.voto_realizado[pt.Txn.sender()].get() == pt.Int(0),
        ),
        pt.Cond(
            [voto.get() == pt.Bytes("A"),
                pt.Seq(
                app.state.total_votos_A.set(app.state.total_votos_A + pt.Int(1)),
                output.set(pt.Concat(pt.Bytes("Voto registrados para: "),voto.get()))
                )
            ],
            [voto.get() == pt.Bytes("B"),
                pt.Seq(app.state.total_votos_B.set(app.state.total_votos_B + pt.Int(1)),
                output.set(pt.Concat(pt.Bytes("Voto registrados para: "), voto.get()))
                )
            ],
        ),
        app.state.voto_realizado[pt.Txn.sender()].set(pt.Int(1)),  
        app.state.total_votantes.increment()
    )

@app.external(read_only=True)
def read_result(voto: pt.abi.String, *, output: pt.abi.Uint64) -> pt.Expr:
    return pt.Cond(
        [voto.get() == pt.Bytes("A"), output.set(app.state.total_votos_A.get())],
        [voto.get() == pt.Bytes("B"), output.set(app.state.total_votos_B.get())],
    )

@app.external(read_only=True)
def read_cantidad_votantes(*, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(app.state.total_votantes.get())

@app.external(read_only=True)
def read_voto(*, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(app.state.voto_realizado[pt.Txn.sender()].get())


if __name__ == "__main__":
    spec = app.build()
    spec.export("artifacts")
