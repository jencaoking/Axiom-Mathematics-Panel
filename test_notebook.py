from mathlab.core.notebook import MathLabNotebook, CellType

if __name__ == '__main__':
    # 1. 创建一个新笔记本
    nb = MathLabNotebook()

    # 2. 添加一段 Markdown 说明
    nb.add_cell(CellType.MARKDOWN, "# 奇异值分解 (SVD) 演示\n这是我的第一篇交互笔记。")

    # 3. 添加第一个代码块：定义矩阵 A
    nb.add_cell(CellType.CODE, "A = [1 2; 3 4; 5 6]")

    # 4. 添加第二个代码块：计算 A 的 SVD（注意它依赖上一个代码块的 A）
    nb.add_cell(CellType.CODE, "svd(A)")

    # 5. 一键执行全部 (Execute All)
    nb.execute_all()

    # 6. 查看执行结果
    for cell in nb.cells:
        print(f"[{cell.execution_count}] {cell.type.name}: {cell.content}")
        for out in cell.outputs:
            print(f"   -> Output: {out['data']}\n")

    # 7. 保存到磁盘
    nb.save_to_file("my_first_note.mlnb")
