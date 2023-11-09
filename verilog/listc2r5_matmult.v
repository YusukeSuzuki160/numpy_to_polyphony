module listc2r5_matmult (
    input wire clk,
    input wire rst,
    input wire matmult_ready,
    input wire matmult_accept,
    output reg matmult_valid,
    input wire signed [63:0] matmult_in_a0,
    input wire signed [63:0] matmult_in_a1,
    input wire signed [63:0] matmult_in_a2,
    input wire signed [63:0] matmult_in_a3,
    input wire signed [63:0] matmult_in_a4,
    input wire signed [63:0] matmult_in_a5,
    input wire signed [63:0] matmult_in_a6,
    input wire signed [63:0] matmult_in_a7,
    input wire signed [63:0] matmult_in_a8,
    input wire signed [63:0] matmult_in_a9,
    output wire signed [63:0] matmult_out_a0,
    output wire signed [63:0] matmult_out_a1,
    output wire signed [63:0] matmult_out_a2,
    output wire signed [63:0] matmult_out_a3,
    output wire signed [63:0] matmult_out_a4,
    output wire signed [63:0] matmult_out_a5,
    output wire signed [63:0] matmult_out_a6,
    output wire signed [63:0] matmult_out_a7,
    output wire signed [63:0] matmult_out_a8,
    output wire signed [63:0] matmult_out_a9,
    input wire signed [63:0] matmult_in_b0,
    input wire signed [63:0] matmult_in_b1,
    input wire signed [63:0] matmult_in_b2,
    input wire signed [63:0] matmult_in_b3,
    input wire signed [63:0] matmult_in_b4,
    input wire signed [63:0] matmult_in_b5,
    input wire signed [63:0] matmult_in_b6,
    input wire signed [63:0] matmult_in_b7,
    input wire signed [63:0] matmult_in_b8,
    input wire signed [63:0] matmult_in_b9,
    output wire signed [63:0] matmult_out_b0,
    output wire signed [63:0] matmult_out_b1,
    output wire signed [63:0] matmult_out_b2,
    output wire signed [63:0] matmult_out_b3,
    output wire signed [63:0] matmult_out_b4,
    output wire signed [63:0] matmult_out_b5,
    output wire signed [63:0] matmult_out_b6,
    output wire signed [63:0] matmult_out_b7,
    output wire signed [63:0] matmult_out_b8,
    output wire signed [63:0] matmult_out_b9,
    input wire [7:0] matmult_in_col,
    input wire signed [63:0] matmult_in_c0,
    input wire signed [63:0] matmult_in_c1,
    input wire signed [63:0] matmult_in_c2,
    input wire signed [63:0] matmult_in_c3,
    input wire signed [63:0] matmult_in_c4,
    input wire signed [63:0] matmult_in_c5,
    input wire signed [63:0] matmult_in_c6,
    input wire signed [63:0] matmult_in_c7,
    input wire signed [63:0] matmult_in_c8,
    input wire signed [63:0] matmult_in_c9,
    input wire signed [63:0] matmult_in_c10,
    input wire signed [63:0] matmult_in_c11,
    input wire signed [63:0] matmult_in_c12,
    input wire signed [63:0] matmult_in_c13,
    input wire signed [63:0] matmult_in_c14,
    input wire signed [63:0] matmult_in_c15,
    input wire signed [63:0] matmult_in_c16,
    input wire signed [63:0] matmult_in_c17,
    input wire signed [63:0] matmult_in_c18,
    input wire signed [63:0] matmult_in_c19,
    input wire signed [63:0] matmult_in_c20,
    input wire signed [63:0] matmult_in_c21,
    input wire signed [63:0] matmult_in_c22,
    input wire signed [63:0] matmult_in_c23,
    input wire signed [63:0] matmult_in_c24,
    output wire signed [63:0] matmult_out_c0,
    output wire signed [63:0] matmult_out_c1,
    output wire signed [63:0] matmult_out_c2,
    output wire signed [63:0] matmult_out_c3,
    output wire signed [63:0] matmult_out_c4,
    output wire signed [63:0] matmult_out_c5,
    output wire signed [63:0] matmult_out_c6,
    output wire signed [63:0] matmult_out_c7,
    output wire signed [63:0] matmult_out_c8,
    output wire signed [63:0] matmult_out_c9,
    output wire signed [63:0] matmult_out_c10,
    output wire signed [63:0] matmult_out_c11,
    output wire signed [63:0] matmult_out_c12,
    output wire signed [63:0] matmult_out_c13,
    output wire signed [63:0] matmult_out_c14,
    output wire signed [63:0] matmult_out_c15,
    output wire signed [63:0] matmult_out_c16,
    output wire signed [63:0] matmult_out_c17,
    output wire signed [63:0] matmult_out_c18,
    output wire signed [63:0] matmult_out_c19,
    output wire signed [63:0] matmult_out_c20,
    output wire signed [63:0] matmult_out_c21,
    output wire signed [63:0] matmult_out_c22,
    output wire signed [63:0] matmult_out_c23,
    output wire signed [63:0] matmult_out_c24
);
    localparam idle = 0;
    localparam fin = 1;
    localparam calc = 2;
    reg [63:0] a[0:9];
    reg [63:0] b[0:9];
    reg [63:0] c[0:9];
    reg [1:0] state;

    assign matmult_out_c0 = c[0];
    assign matmult_out_c1 = c[1];
    assign matmult_out_c2 = c[2];
    assign matmult_out_c3 = c[3];
    assign matmult_out_c4 = c[4];
    assign matmult_out_c5 = c[5];
    assign matmult_out_c6 = c[6];
    assign matmult_out_c7 = c[7];
    assign matmult_out_c8 = c[8];
    assign matmult_out_c9 = c[9];
    assign matmult_out_c10 = c[10];
    assign matmult_out_c11 = c[11];
    assign matmult_out_c12 = c[12];
    assign matmult_out_c13 = c[13];
    assign matmult_out_c14 = c[14];
    assign matmult_out_c15 = c[15];
    assign matmult_out_c16 = c[16];
    assign matmult_out_c17 = c[17];
    assign matmult_out_c18 = c[18];
    assign matmult_out_c19 = c[19];
    assign matmult_out_c20 = c[20];
    assign matmult_out_c21 = c[21];
    assign matmult_out_c22 = c[22];
    assign matmult_out_c23 = c[23];
    assign matmult_out_c24 = c[24];

    always @(posedge clk) begin
        if (rst) begin
            for (integer i = 0; i < 10; i++) begin
    a[i] <= 0;
end
            for (integer i = 0; i < 10; i++) begin
    b[i] <= 0;
end
            for (integer i = 0; i < 10; i++) begin
    c[i] <= 0;
end
            state <= 0;
            matmult_valid <= 0;
        end else begin
            case (state)
                idle: begin
                    matmult_valid <= 0;
                    if (matmult_ready) begin
    a[0] <= matmult_in_a0;
    a[1] <= matmult_in_a1;
    a[2] <= matmult_in_a2;
    a[3] <= matmult_in_a3;
    a[4] <= matmult_in_a4;
    a[5] <= matmult_in_a5;
    a[6] <= matmult_in_a6;
    a[7] <= matmult_in_a7;
    a[8] <= matmult_in_a8;
    a[9] <= matmult_in_a9;
    b[0] <= matmult_in_b0;
    b[1] <= matmult_in_b1;
    b[2] <= matmult_in_b2;
    b[3] <= matmult_in_b3;
    b[4] <= matmult_in_b4;
    b[5] <= matmult_in_b5;
    b[6] <= matmult_in_b6;
    b[7] <= matmult_in_b7;
    b[8] <= matmult_in_b8;
    b[9] <= matmult_in_b9;
end

                end
                fin: begin
                    matmult_valid <= 1;
                end
                calc: begin
                    c[0] <= a[0] * b[0] + a[1] * b[5];
                    c[1] <= a[0] * b[1] + a[1] * b[6];
                    c[2] <= a[0] * b[2] + a[1] * b[7];
                    c[3] <= a[0] * b[3] + a[1] * b[8];
                    c[4] <= a[0] * b[4] + a[1] * b[9];
                    c[5] <= a[2] * b[0] + a[3] * b[5];
                    c[6] <= a[2] * b[1] + a[3] * b[6];
                    c[7] <= a[2] * b[2] + a[3] * b[7];
                    c[8] <= a[2] * b[3] + a[3] * b[8];
                    c[9] <= a[2] * b[4] + a[3] * b[9];
                    c[10] <= a[4] * b[0] + a[5] * b[5];
                    c[11] <= a[4] * b[1] + a[5] * b[6];
                    c[12] <= a[4] * b[2] + a[5] * b[7];
                    c[13] <= a[4] * b[3] + a[5] * b[8];
                    c[14] <= a[4] * b[4] + a[5] * b[9];
                    c[15] <= a[6] * b[0] + a[7] * b[5];
                    c[16] <= a[6] * b[1] + a[7] * b[6];
                    c[17] <= a[6] * b[2] + a[7] * b[7];
                    c[18] <= a[6] * b[3] + a[7] * b[8];
                    c[19] <= a[6] * b[4] + a[7] * b[9];
                    c[20] <= a[8] * b[0] + a[9] * b[5];
                    c[21] <= a[8] * b[1] + a[9] * b[6];
                    c[22] <= a[8] * b[2] + a[9] * b[7];
                    c[23] <= a[8] * b[3] + a[9] * b[8];
                    c[24] <= a[8] * b[4] + a[9] * b[9];
                end
            endcase
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            state <= 0;
        end else begin
            case (state)
                fin: begin
                    if (matmult_accept) begin
                        state <= idle;
                    end
                end
                idle: begin
                    if (matmult_ready) begin
                        state <= calc;
                    end
                end
                calc: begin
                    state <= fin;
                end
            endcase
        end
    end

endmodule
