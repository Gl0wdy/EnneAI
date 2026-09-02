from enneai.ai.rag import retrieve


async def test_retrieve():
    result = await retrieve('SO5', rerank_top_n=10)
    assert result.is_empty == False


async def test_retrieve_category():
    cats = ['ennea', 'psychosophy', 'socio', 'jungian']

    for cat in cats:
        result = await retrieve(f'{cat} query', rerank_top_n=10, category=cat)

        assert result.is_empty == False, f'{cat} collection is empty'

        for chunk in result.chunks:
            assert chunk['category'] == cat, f'{chunk["category"]} != {cat}'