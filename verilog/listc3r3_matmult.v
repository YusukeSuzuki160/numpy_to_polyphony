module listc3r3_matmult (
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
    output wire signed [63:0] matmult_out_a0,
    output wire signed [63:0] matmult_out_a1,
    output wire signed [63:0] matmult_out_a2,
    output wire signed [63:0] matmult_out_a3,
    output wire signed [63:0] matmult_out_a4,
    output wire signed [63:0] matmult_out_a5,
    output wire signed [63:0] matmult_out_a6,
    output wire signed [63:0] matmult_out_a7,
    output wire signed [63:0] matmult_out_a8,
    input wire signed [63:0] matmult_in_b0,
    input wire signed [63:0] matmult_in_b1,
    input wire signed [63:0] matmult_in_b2,
    input wire signed [63:0] matmult_in_b3,
    input wire signed [63:0] matmult_in_b4,
    input wire signed [63:0] matmult_in_b5,
    input wire signed [63:0] matmult_in_b6,
    input wire signed [63:0] matmult_in_b7,
    input wire signed [63:0] matmult_in_b8,
    output wire signed [63:0] matmult_out_b0,
    output wire signed [63:0] matmult_out_b1,
    output wire signed [63:0] matmult_out_b2,
    output wire signed [63:0] matmult_out_b3,
    output wire signed [63:0] matmult_out_b4,
    output wire signed [63:0] matmult_out_b5,
    output wire signed [63:0] matmult_out_b6,
    output wire signed [63:0] matmult_out_b7,
    output wire signed [63:0] matmult_out_b8,
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
  reg [63:0] a[0:8];
  reg [63:0] b[0:8];
  reg [63:0] c[0:8];
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
      for (integer i = 0; i < 9; i++) begin
        a[i] <= 0;
      end
      for (integer i = 0; i < 9; i++) begin
        b[i] <= 0;
      end
      for (integer i = 0; i < 9; i++) begin
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
            b[0] <= matmult_in_b0;
            b[1] <= matmult_in_b1;
            b[2] <= matmult_in_b2;
            b[3] <= matmult_in_b3;
            b[4] <= matmult_in_b4;
            b[5] <= matmult_in_b5;
            b[6] <= matmult_in_b6;
            b[7] <= matmult_in_b7;
            b[8] <= matmult_in_b8;
          end

        end
        fin: begin
          matmult_valid <= 1;
        end
        calc: begin
          c[0] <= a[0] * b[0] + a[1] * b[3] + a[2] * b[6];
          c[1] <= a[0] * b[1] + a[1] * b[4] + a[2] * b[7];
          c[2] <= a[0] * b[2] + a[1] * b[5] + a[2] * b[8];
          c[3] <= a[3] * b[0] + a[4] * b[3] + a[5] * b[6];
          c[4] <= a[3] * b[1] + a[4] * b[4] + a[5] * b[7];
          c[5] <= a[3] * b[2] + a[4] * b[5] + a[5] * b[8];
          c[6] <= a[6] * b[0] + a[7] * b[3] + a[8] * b[6];
          c[7] <= a[6] * b[1] + a[7] * b[4] + a[8] * b[7];
          c[8] <= a[6] * b[2] + a[7] * b[5] + a[8] * b[8];
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
