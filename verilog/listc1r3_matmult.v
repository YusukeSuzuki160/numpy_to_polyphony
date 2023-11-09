module listc1r3_matmult (
    input wire clk,
    input wire rst,
    input wire matmult_ready,
    input wire matmult_accept,
    output reg matmult_valid,
    input wire signed [63:0] matmult_in_a0,
    input wire signed [63:0] matmult_in_a1,
    input wire signed [63:0] matmult_in_a2,
    output wire signed [63:0] matmult_out_a0,
    output wire signed [63:0] matmult_out_a1,
    output wire signed [63:0] matmult_out_a2,
    input wire signed [63:0] matmult_in_b0,
    input wire signed [63:0] matmult_in_b1,
    input wire signed [63:0] matmult_in_b2,
    output wire signed [63:0] matmult_out_b0,
    output wire signed [63:0] matmult_out_b1,
    output wire signed [63:0] matmult_out_b2,
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
    output wire signed [63:0] matmult_out_c0,
    output wire signed [63:0] matmult_out_c1,
    output wire signed [63:0] matmult_out_c2,
    output wire signed [63:0] matmult_out_c3,
    output wire signed [63:0] matmult_out_c4,
    output wire signed [63:0] matmult_out_c5,
    output wire signed [63:0] matmult_out_c6,
    output wire signed [63:0] matmult_out_c7,
    output wire signed [63:0] matmult_out_c8
);
    localparam idle = 0;
    localparam fin = 1;
    localparam calc = 2;
    reg [63:0] a[0:2];
    reg [63:0] b[0:2];
    reg [63:0] c[0:2];
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

    always @(posedge clk) begin
        if (rst) begin
            for (integer i = 0; i < 3; i++) begin
    a[i] <= 0;
end
            for (integer i = 0; i < 3; i++) begin
    b[i] <= 0;
end
            for (integer i = 0; i < 3; i++) begin
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
    b[0] <= matmult_in_b0;
    b[1] <= matmult_in_b1;
    b[2] <= matmult_in_b2;
end

                end
                fin: begin
                    matmult_valid <= 1;
                end
                calc: begin
                    c[0] <= a[0] * b[0];
                    c[1] <= a[0] * b[1];
                    c[2] <= a[0] * b[2];
                    c[3] <= a[1] * b[0];
                    c[4] <= a[1] * b[1];
                    c[5] <= a[1] * b[2];
                    c[6] <= a[2] * b[0];
                    c[7] <= a[2] * b[1];
                    c[8] <= a[2] * b[2];
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
